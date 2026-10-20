"""Validity gates for randomized experiment analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import chisquare, norm, ttest_ind

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


@dataclass(frozen=True, slots=True)
class EffectEstimate:
    """Treatment-minus-control estimate with transparent inference metadata."""

    treatment_name: str
    control_name: str
    treatment_mean: float
    control_mean: float
    absolute_effect: float
    relative_effect: float | None
    ci_low: float
    ci_high: float
    p_value: float
    adjusted_p_value: float | None
    n_treatment: int
    n_control: int
    method: str


def _finite_array(values: Sequence[float], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional sample")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains missing values or non-finite values")
    return array


def proportion_effect(
    treatment: Sequence[float],
    control: Sequence[float],
    *,
    treatment_name: str = "treatment",
    control_name: str = "control",
    confidence: float = 0.95,
) -> EffectEstimate:
    """Estimate a binary risk difference with an unpooled CI and pooled z-test."""

    treatment_values = _finite_array(treatment, "treatment")
    control_values = _finite_array(control, "control")
    if not set(np.unique(treatment_values)).issubset({0.0, 1.0}) or not set(
        np.unique(control_values)
    ).issubset({0.0, 1.0}):
        raise ValueError("proportion samples must contain only 0 and 1")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    treatment_mean = float(treatment_values.mean())
    control_mean = float(control_values.mean())
    difference = treatment_mean - control_mean
    interval_se = np.sqrt(
        treatment_mean * (1 - treatment_mean) / len(treatment_values)
        + control_mean * (1 - control_mean) / len(control_values)
    )
    critical_value = float(norm.ppf(1 - (1 - confidence) / 2))
    pooled = float(
        (treatment_values.sum() + control_values.sum())
        / (len(treatment_values) + len(control_values))
    )
    test_se = np.sqrt(
        pooled
        * (1 - pooled)
        * (1 / len(treatment_values) + 1 / len(control_values))
    )
    if test_se == 0:
        p_value = 1.0 if difference == 0 else 0.0
    else:
        p_value = float(2 * norm.sf(abs(difference / test_se)))
    relative = difference / control_mean if control_mean != 0 else None
    return EffectEstimate(
        treatment_name=treatment_name,
        control_name=control_name,
        treatment_mean=treatment_mean,
        control_mean=control_mean,
        absolute_effect=difference,
        relative_effect=relative,
        ci_low=float(difference - critical_value * interval_se),
        ci_high=float(difference + critical_value * interval_se),
        p_value=p_value,
        adjusted_p_value=None,
        n_treatment=len(treatment_values),
        n_control=len(control_values),
        method="difference_in_proportions",
    )


def bootstrap_mean_effect(
    treatment: Sequence[float],
    control: Sequence[float],
    *,
    treatment_name: str = "treatment",
    control_name: str = "control",
    confidence: float = 0.95,
    n_resamples: int = 5000,
    seed: int = 20261019,
) -> EffectEstimate:
    """Estimate a mean difference with a percentile bootstrap and Welch p-value."""

    treatment_values = _finite_array(treatment, "treatment")
    control_values = _finite_array(control, "control")
    if n_resamples < 100:
        raise ValueError("n_resamples must be at least 100")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    rng = np.random.default_rng(seed)
    treatment_indices = rng.integers(
        0, len(treatment_values), size=(n_resamples, len(treatment_values))
    )
    control_indices = rng.integers(0, len(control_values), size=(n_resamples, len(control_values)))
    bootstrap_effects = (
        treatment_values[treatment_indices].mean(axis=1)
        - control_values[control_indices].mean(axis=1)
    )
    tail = (1 - confidence) / 2
    ci_low, ci_high = np.quantile(bootstrap_effects, [tail, 1 - tail])
    treatment_mean = float(treatment_values.mean())
    control_mean = float(control_values.mean())
    difference = treatment_mean - control_mean
    test = ttest_ind(treatment_values, control_values, equal_var=False)
    relative = difference / control_mean if control_mean != 0 else None
    return EffectEstimate(
        treatment_name=treatment_name,
        control_name=control_name,
        treatment_mean=treatment_mean,
        control_mean=control_mean,
        absolute_effect=difference,
        relative_effect=relative,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        p_value=float(test.pvalue),
        adjusted_p_value=None,
        n_treatment=len(treatment_values),
        n_control=len(control_values),
        method="bootstrap_percentile_welch",
    )


def holm_adjust(p_values: Sequence[float]) -> np.ndarray:
    """Return Holm step-down adjusted p-values in their original order."""

    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("p_values must be a non-empty one-dimensional sequence")
    if not np.isfinite(values).all():
        raise ValueError("p_values must be finite")
    if ((values < 0) | (values > 1)).any():
        raise ValueError("p_values must be between 0 and 1")
    order = np.argsort(values)
    ordered = values[order]
    scaled = (len(values) - np.arange(len(values))) * ordered
    monotone = np.minimum(1.0, np.maximum.accumulate(scaled))
    adjusted = np.empty_like(monotone)
    adjusted[order] = monotone
    return adjusted


def cuped_adjust(outcome: Sequence[float], covariate: Sequence[float]) -> np.ndarray:
    """Apply one-covariate CUPED while preserving the original outcome mean."""

    outcome_values = _finite_array(outcome, "outcome")
    covariate_values = _finite_array(covariate, "covariate")
    if len(outcome_values) != len(covariate_values):
        raise ValueError("outcome and covariate must have the same length")
    covariate_variance = float(np.var(covariate_values, ddof=1))
    if covariate_variance == 0 or np.isnan(covariate_variance):
        return outcome_values.copy()
    theta = float(np.cov(outcome_values, covariate_values, ddof=1)[0, 1]) / covariate_variance
    return outcome_values - theta * (covariate_values - covariate_values.mean())


def interaction_effects(
    frame: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    subgroup_col: str,
    *,
    min_group_size: int = 30,
) -> pd.DataFrame:
    """Estimate labeled exploratory subgroup effects with per-arm size guards."""

    required = {outcome_col, treatment_col, subgroup_col}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing interaction columns: {', '.join(missing)}")
    if min_group_size < 2:
        raise ValueError("min_group_size must be at least 2")
    working = frame.loc[:, [outcome_col, treatment_col, subgroup_col]].copy()
    if working.isna().any().any():
        raise ValueError("interaction data contains missing values")
    if not set(working[treatment_col].unique()).issubset({0, 1}):
        raise ValueError("treatment column must contain only 0 and 1")
    overall_treatment = working.loc[working[treatment_col].astype(bool), outcome_col].astype(float)
    overall_control = working.loc[~working[treatment_col].astype(bool), outcome_col].astype(float)
    overall_effect = float(overall_treatment.mean() - overall_control.mean())

    rows: list[dict[str, object]] = []
    for subgroup, group in working.groupby(subgroup_col, sort=True):
        treatment_values = group.loc[group[treatment_col].astype(bool), outcome_col].astype(float)
        control_values = group.loc[~group[treatment_col].astype(bool), outcome_col].astype(float)
        eligible = len(treatment_values) >= min_group_size and len(control_values) >= min_group_size
        if eligible:
            effect = float(treatment_values.mean() - control_values.mean())
            constant_arms = treatment_values.var(ddof=1) == 0 and control_values.var(ddof=1) == 0
            if constant_arms:
                p_value = 1.0 if effect == 0 else 0.0
            else:
                p_value = float(
                    ttest_ind(treatment_values, control_values, equal_var=False).pvalue
                )
            interaction = effect - overall_effect
        else:
            effect = np.nan
            p_value = np.nan
            interaction = np.nan
        rows.append(
            {
                "subgroup": subgroup,
                "n_treatment": len(treatment_values),
                "n_control": len(control_values),
                "treatment_mean": float(treatment_values.mean()),
                "control_mean": float(control_values.mean()),
                "effect": effect,
                "interaction_effect": interaction,
                "p_value": p_value,
                "eligible": eligible,
                "interpretation": "exploratory_interaction",
            }
        )
    return pd.DataFrame(rows)


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
