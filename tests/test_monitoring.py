from datetime import date

import numpy as np
import pandas as pd

from growthlens.monitoring import DateRange, attribute_change, detect_robust_anomalies


def _series(values: list[float], start: str = "2024-01-01") -> pd.Series:
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="D"))


def test_constant_series_with_zero_mad_is_not_anomalous() -> None:
    result = detect_robust_anomalies(_series([10.0] * 8), window=5, threshold=3.5, min_periods=3)

    assert result.iloc[-1]["baseline"] == 10.0
    assert result.iloc[-1]["score"] == 0.0
    assert bool(result.iloc[-1]["is_anomaly"]) is False
    assert result.iloc[-1]["direction"] == "stable"


def test_missing_days_are_materialized_and_never_flagged() -> None:
    series = pd.Series(
        [10.0, 11.0, 10.0],
        index=pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-04"]),
    )

    result = detect_robust_anomalies(series, window=3, threshold=3.5, min_periods=2)

    assert list(result.index) == list(pd.date_range("2024-01-01", "2024-01-04", freq="D"))
    assert np.isnan(result.loc["2024-01-02", "actual"])
    assert bool(result.loc["2024-01-02", "is_anomaly"]) is False
    assert result.loc["2024-01-02", "direction"] == "missing"


def test_insufficient_history_has_no_score_or_alert() -> None:
    result = detect_robust_anomalies(_series([10.0, 11.0]), window=5, threshold=3.5, min_periods=3)

    assert result["baseline"].isna().all()
    assert result["score"].isna().all()
    assert result["is_anomaly"].eq(False).all()


def test_known_spike_and_drop_are_flagged_with_direction() -> None:
    spike = detect_robust_anomalies(
        _series([10.0, 10.0, 10.0, 10.0, 30.0]),
        window=4,
        threshold=3.5,
        min_periods=4,
    )
    drop = detect_robust_anomalies(
        _series([10.0, 10.0, 10.0, 10.0, 0.0]),
        window=4,
        threshold=3.5,
        min_periods=4,
    )

    assert bool(spike.iloc[-1]["is_anomaly"]) is True
    assert spike.iloc[-1]["score"] == np.inf
    assert spike.iloc[-1]["direction"] == "up"
    assert bool(drop.iloc[-1]["is_anomaly"]) is True
    assert drop.iloc[-1]["score"] == -np.inf
    assert drop.iloc[-1]["direction"] == "down"


def test_zero_baseline_with_nonzero_actual_is_explicit_anomaly() -> None:
    result = detect_robust_anomalies(
        _series([0.0, 0.0, 0.0, 5.0]),
        window=3,
        threshold=3.5,
        min_periods=3,
    )

    assert result.iloc[-1]["baseline"] == 0.0
    assert result.iloc[-1]["score"] == np.inf
    assert bool(result.iloc[-1]["is_anomaly"]) is True


def test_attribution_contributions_sum_to_total_period_change() -> None:
    frame = pd.DataFrame(
        {
            "period": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-01-08", "2024-01-08"]
            ),
            "state": ["SP", "RJ", "SP", "RJ"],
            "value": [100.0, 50.0, 80.0, 90.0],
        }
    )

    result = attribute_change(
        frame,
        value_col="value",
        dimension_col="state",
        before=DateRange(date(2024, 1, 1), date(2024, 1, 7)),
        after=DateRange(date(2024, 1, 8), date(2024, 1, 14)),
    )

    assert result.set_index("state")["change"].to_dict() == {"RJ": 40.0, "SP": -20.0}
    assert result["change"].sum() == 20.0
    assert result["contribution_share"].sum() == 1.0
