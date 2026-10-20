import numpy as np
import pandas as pd
import pytest

from growthlens.experimentation import (
    bootstrap_mean_effect,
    cuped_adjust,
    holm_adjust,
    interaction_effects,
    proportion_effect,
)


def test_proportion_effect_is_zero_for_identical_samples() -> None:
    treatment = np.array([0, 1] * 50)
    control = np.array([0, 1] * 50)

    estimate = proportion_effect(treatment, control, treatment_name="email", control_name="none")

    assert estimate.absolute_effect == 0.0
    assert estimate.relative_effect == 0.0
    assert estimate.p_value == 1.0
    assert estimate.ci_low < 0 < estimate.ci_high
    assert estimate.n_treatment == estimate.n_control == 100
    assert estimate.method == "difference_in_proportions"


def test_proportion_effect_recovers_known_positive_difference() -> None:
    treatment = np.array([1] * 70 + [0] * 30)
    control = np.array([1] * 40 + [0] * 60)

    estimate = proportion_effect(treatment, control)

    assert estimate.absolute_effect == pytest.approx(0.30)
    assert estimate.relative_effect == pytest.approx(0.75)
    assert estimate.ci_low > 0
    assert estimate.p_value < 0.001


def test_bootstrap_mean_effect_is_deterministic_for_zero_inflated_spend() -> None:
    treatment = np.array([0.0] * 80 + [10.0] * 20)
    control = np.array([0.0] * 90 + [5.0] * 10)

    first = bootstrap_mean_effect(treatment, control, n_resamples=2000, seed=20261019)
    second = bootstrap_mean_effect(treatment, control, n_resamples=2000, seed=20261019)

    assert first == second
    assert first.absolute_effect == pytest.approx(1.5)
    assert first.relative_effect == pytest.approx(3.0)
    assert first.ci_low > 0
    assert first.method == "bootstrap_percentile_welch"


def test_holm_adjust_preserves_input_order_and_monotonic_family_control() -> None:
    adjusted = holm_adjust([0.01, 0.04, 0.02])

    np.testing.assert_allclose(adjusted, [0.03, 0.04, 0.04])


def test_cuped_reduces_variance_for_correlated_pre_treatment_covariate() -> None:
    rng = np.random.default_rng(42)
    covariate = rng.normal(size=1000)
    outcome = 4.0 * covariate + rng.normal(scale=1.0, size=1000)

    adjusted = cuped_adjust(outcome, covariate)

    assert np.var(adjusted, ddof=1) < np.var(outcome, ddof=1) * 0.2
    assert np.mean(adjusted) == pytest.approx(np.mean(outcome))


def test_cuped_constant_covariate_returns_copy_of_outcome() -> None:
    outcome = np.array([1.0, 2.0, 3.0])

    adjusted = cuped_adjust(outcome, np.ones(3))

    np.testing.assert_array_equal(adjusted, outcome)
    assert adjusted is not outcome


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: proportion_effect([0, np.nan], [0, 1]), "missing values"),
        (lambda: bootstrap_mean_effect([0.0, np.nan], [0.0, 1.0]), "missing values"),
        (lambda: cuped_adjust([1.0, np.nan], [1.0, 2.0]), "missing values"),
        (lambda: holm_adjust([0.1, np.nan]), "finite"),
    ],
)
def test_estimators_reject_missing_values(call: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        call()  # type: ignore[operator]


def test_interactions_enforce_minimum_sample_per_arm() -> None:
    frame = pd.DataFrame(
        {
            "subgroup": ["A"] * 40 + ["B"] * 40 + ["small"] * 4,
            "treated": ([0] * 20 + [1] * 20) * 2 + [0, 0, 1, 1],
            "outcome": [0.0] * 20 + [1.0] * 20 + [0.0] * 40 + [0.0, 0.0, 1.0, 1.0],
        }
    )

    result = interaction_effects(
        frame,
        outcome_col="outcome",
        treatment_col="treated",
        subgroup_col="subgroup",
        min_group_size=10,
    ).set_index("subgroup")

    assert bool(result.loc["A", "eligible"]) is True
    assert result.loc["A", "effect"] == 1.0
    assert result.loc["A", "interaction_effect"] > 0
    assert result.loc["A", "p_value"] == 0.0
    assert result.loc["B", "interaction_effect"] < 0
    assert result.loc["B", "p_value"] == 1.0
    assert bool(result.loc["small", "eligible"]) is False
    assert np.isnan(result.loc["small", "effect"])
