"""Robust KPI anomaly detection and additive change attribution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

MAD_NORMALIZATION = 0.6744897501960817


@dataclass(frozen=True, slots=True)
class DateRange:
    """Inclusive calendar range used for before/after comparisons."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("DateRange end must not precede start")


@dataclass(frozen=True, slots=True)
class Alert:
    """Serializable anomaly evidence for one metric and period."""

    metric: str
    period: date
    actual: float
    baseline: float
    score: float
    direction: str


def _median_absolute_deviation(values: np.ndarray) -> float:
    median = np.nanmedian(values)
    return float(np.nanmedian(np.abs(values - median)))


def detect_robust_anomalies(
    series: pd.Series,
    window: int,
    threshold: float,
    min_periods: int,
) -> pd.DataFrame:
    """Score a daily series against a trailing median/MAD that excludes today."""

    if window < 1:
        raise ValueError("window must be positive")
    if not 1 <= min_periods <= window:
        raise ValueError("min_periods must be between 1 and window")
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("series index must be a DatetimeIndex")
    if series.index.has_duplicates:
        raise ValueError("series index must be unique")

    values = pd.to_numeric(series, errors="coerce").sort_index()
    if values.empty:
        return pd.DataFrame(
            columns=["actual", "baseline", "mad", "score", "direction", "is_anomaly"],
            index=pd.DatetimeIndex([], name=series.index.name),
        )
    values = values.reindex(pd.date_range(values.index.min(), values.index.max(), freq="D"))
    history = values.shift(1)
    rolling = history.rolling(window=window, min_periods=min_periods)
    baseline = rolling.median()
    mad = rolling.apply(_median_absolute_deviation, raw=True)

    scores: list[float] = []
    directions: list[str] = []
    anomalies: list[bool] = []
    for actual, center, dispersion in zip(values, baseline, mad, strict=True):
        if pd.isna(actual):
            score = np.nan
            direction = "missing"
        elif pd.isna(center) or pd.isna(dispersion):
            score = np.nan
            direction = "insufficient_history"
        else:
            delta = float(actual - center)
            direction = "up" if delta > 0 else "down" if delta < 0 else "stable"
            if dispersion == 0:
                score = 0.0 if delta == 0 else float(np.copysign(np.inf, delta))
            else:
                score = float(MAD_NORMALIZATION * delta / dispersion)
        scores.append(score)
        anomalies.append(bool(not pd.isna(score) and abs(score) >= threshold))
        directions.append(direction)

    return pd.DataFrame(
        {
            "actual": values,
            "baseline": baseline,
            "mad": mad,
            "score": scores,
            "direction": directions,
            "is_anomaly": anomalies,
        },
        index=values.index,
    )


def attribute_change(
    frame: pd.DataFrame,
    value_col: str,
    dimension_col: str,
    before: DateRange,
    after: DateRange,
) -> pd.DataFrame:
    """Attribute an additive value change across a categorical dimension."""

    required = {"period", value_col, dimension_col}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing attribution columns: {', '.join(missing)}")
    working = frame.loc[:, ["period", value_col, dimension_col]].copy()
    working["period"] = pd.to_datetime(working["period"])
    periods = working["period"].dt.date
    before_values = (
        working.loc[periods.between(before.start, before.end)]
        .groupby(dimension_col, dropna=False)[value_col]
        .sum()
        .rename("before_value")
    )
    after_values = (
        working.loc[periods.between(after.start, after.end)]
        .groupby(dimension_col, dropna=False)[value_col]
        .sum()
        .rename("after_value")
    )
    result = pd.concat([before_values, after_values], axis=1).fillna(0.0)
    result["change"] = result["after_value"] - result["before_value"]
    total_change = float(result["change"].sum())
    result["contribution_share"] = (
        result["change"] / total_change if total_change != 0 else 0.0
    )
    result = result.reset_index()
    return result.sort_values(
        ["change", dimension_col], ascending=[False, True], ignore_index=True
    )
