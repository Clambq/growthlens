"""Validity gates for randomized experiment analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import chisquare

POST_TREATMENT_COLUMNS = frozenset({"visit", "conversion", "spend"})


@dataclass(frozen=True, slots=True)
class SampleRatioResult:
    """Chi-square sample-ratio-mismatch diagnostic."""

    observed: Mapping[str, int]
    expected_counts: Mapping[str, float]
    statistic: float
    p_value: float
    alpha: float
    passes: bool


@dataclass(frozen=True, slots=True)
class BalanceResult:
    """Summary of a standardized-mean-difference table."""

    table: pd.DataFrame
    max_abs_smd: float
    passes: bool


def sample_ratio_test(
    observed: Mapping[str, int],
    expected: Mapping[str, float],
    *,
    alpha: float = 0.01,
) -> SampleRatioResult:
    """Test observed group counts against pre-specified allocation shares."""

    if set(observed) != set(expected):
        raise ValueError("observed and expected groups must match")
    if not observed:
        raise ValueError("at least one experiment group is required")
    if any(count <= 0 for count in observed.values()):
        raise ValueError("all observed experiment groups must have positive counts")
    if any(share <= 0 for share in expected.values()):
        raise ValueError("all expected shares must be positive")
    if not np.isclose(sum(expected.values()), 1.0, atol=1e-9):
        raise ValueError("expected shares must sum to 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    groups = sorted(observed)
    total = sum(observed.values())
    expected_counts = {group: total * expected[group] for group in groups}
    result = chisquare(
        [observed[group] for group in groups],
        f_exp=[expected_counts[group] for group in groups],
    )
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    return SampleRatioResult(
        observed=dict(observed),
        expected_counts=expected_counts,
        statistic=statistic,
        p_value=p_value,
        alpha=alpha,
        passes=p_value >= alpha,
    )


def validate_assignments(
    frame: pd.DataFrame,
    customer_col: str,
    group_col: str,
    expected_groups: Set[str] | set[str],
) -> None:
    """Reject duplicate/conflicting assignments and missing randomized arms."""

    missing_columns = {customer_col, group_col}.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"missing assignment columns: {', '.join(sorted(missing_columns))}")
    observed_groups = set(frame[group_col].dropna().astype(str))
    missing_groups = sorted(set(expected_groups).difference(observed_groups))
    if missing_groups:
        raise ValueError(f"missing experiment groups: {', '.join(missing_groups)}")
    unexpected_groups = sorted(observed_groups.difference(expected_groups))
    if unexpected_groups:
        raise ValueError(f"unexpected experiment groups: {', '.join(unexpected_groups)}")

    group_counts = frame.groupby(customer_col, dropna=False)[group_col].nunique()
    conflicting = sorted(str(value) for value in group_counts[group_counts > 1].index)
    if conflicting:
        raise ValueError(
            "customers assigned to multiple experiment groups: " + ", ".join(conflicting)
        )
    duplicate_mask = frame[customer_col].duplicated()
    duplicated = sorted(str(value) for value in frame.loc[duplicate_mask, customer_col])
    if duplicated:
        raise ValueError(f"duplicate customer assignments: {', '.join(duplicated)}")


def validate_adjustment_covariates(covariates: Sequence[str]) -> tuple[str, ...]:
    """Return normalized covariates after blocking post-treatment leakage."""

    normalized = tuple(str(value) for value in covariates)
    normalized_lower = {value.lower() for value in normalized}
    prohibited = sorted(normalized_lower.intersection(POST_TREATMENT_COLUMNS))
    if prohibited:
        raise ValueError(
            "post-treatment adjustment covariates are prohibited: " + ", ".join(prohibited)
        )
    if len(set(normalized)) != len(normalized):
        raise ValueError("adjustment covariates must be unique")
    return normalized


def standardized_mean_differences(
    frame: pd.DataFrame,
    group_col: str,
    covariates: Sequence[str],
    reference: str,
) -> pd.DataFrame:
    """Compare each arm with a reference using pooled-standard-deviation SMDs."""

    covariates = validate_adjustment_covariates(covariates)
    missing = sorted({group_col, *covariates}.difference(frame.columns))
    if missing:
        raise ValueError(f"missing balance columns: {', '.join(missing)}")
    groups = sorted(str(value) for value in frame[group_col].dropna().unique())
    if reference not in groups:
        raise ValueError(f"reference group not found: {reference}")
    comparisons = [group for group in groups if group != reference]
    if not comparisons:
        raise ValueError("at least one non-reference group is required")

    rows: list[dict[str, object]] = []
    reference_rows = frame.loc[frame[group_col] == reference]
    for group in comparisons:
        group_rows = frame.loc[frame[group_col] == group]
        for covariate in covariates:
            reference_values = pd.to_numeric(reference_rows[covariate], errors="raise").dropna()
            group_values = pd.to_numeric(group_rows[covariate], errors="raise").dropna()
            if len(reference_values) < 2 or len(group_values) < 2:
                raise ValueError(f"covariate {covariate} needs at least two values per group")
            reference_mean = float(reference_values.mean())
            group_mean = float(group_values.mean())
            pooled_sd = float(
                np.sqrt((reference_values.var(ddof=1) + group_values.var(ddof=1)) / 2)
            )
            difference = group_mean - reference_mean
            if pooled_sd == 0:
                smd = 0.0 if difference == 0 else float(np.copysign(np.inf, difference))
            else:
                smd = difference / pooled_sd
            rows.append(
                {
                    "group": group,
                    "reference": reference,
                    "covariate": covariate,
                    "group_mean": group_mean,
                    "reference_mean": reference_mean,
                    "smd": smd,
                    "abs_smd": abs(smd),
                    "balanced": abs(smd) < 0.1,
                }
            )
    return pd.DataFrame(rows)
