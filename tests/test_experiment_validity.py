import pandas as pd
import pytest

from growthlens.experimentation import (
    sample_ratio_test,
    standardized_mean_differences,
    validate_adjustment_covariates,
    validate_assignments,
)


def test_valid_three_way_split_passes_sample_ratio_check() -> None:
    result = sample_ratio_test(
        {"Mens E-Mail": 21333, "Womens E-Mail": 21333, "No E-Mail": 21334},
        {"Mens E-Mail": 1 / 3, "Womens E-Mail": 1 / 3, "No E-Mail": 1 / 3},
    )

    assert result.passes is True
    assert result.p_value > 0.99
    assert sum(result.expected_counts.values()) == pytest.approx(64000)


def test_deliberate_sample_ratio_mismatch_fails() -> None:
    result = sample_ratio_test(
        {"Mens E-Mail": 30000, "Womens E-Mail": 17000, "No E-Mail": 17000},
        {"Mens E-Mail": 1 / 3, "Womens E-Mail": 1 / 3, "No E-Mail": 1 / 3},
    )

    assert result.passes is False
    assert result.p_value < 0.001


def test_expected_shares_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        sample_ratio_test({"A": 10, "B": 10}, {"A": 0.4, "B": 0.4})


def test_missing_expected_group_is_rejected() -> None:
    with pytest.raises(ValueError, match="observed and expected groups must match"):
        sample_ratio_test({"A": 10}, {"A": 0.5, "B": 0.5})


def test_duplicate_customer_assignment_is_rejected() -> None:
    assignments = pd.DataFrame(
        {"customer_id": ["c1", "c1", "c2"], "segment": ["A", "B", "A"]}
    )

    with pytest.raises(ValueError, match="multiple experiment groups: c1"):
        validate_assignments(assignments, "customer_id", "segment", {"A", "B"})


def test_missing_assignment_group_is_rejected() -> None:
    assignments = pd.DataFrame({"customer_id": ["c1", "c2"], "segment": ["A", "A"]})

    with pytest.raises(ValueError, match="missing experiment groups: B"):
        validate_assignments(assignments, "customer_id", "segment", {"A", "B"})


def test_balanced_covariates_have_small_standardized_differences() -> None:
    frame = pd.DataFrame(
        {
            "segment": ["control"] * 4 + ["treatment"] * 4,
            "history": [90.0, 100.0, 110.0, 100.0, 92.0, 102.0, 108.0, 98.0],
            "recency": [2.0, 4.0, 6.0, 8.0, 2.0, 4.0, 6.0, 8.0],
        }
    )

    result = standardized_mean_differences(
        frame, "segment", ["history", "recency"], reference="control"
    )

    assert result["abs_smd"].max() < 0.1
    assert result["balanced"].all()


def test_imbalanced_covariate_is_flagged() -> None:
    frame = pd.DataFrame(
        {
            "segment": ["control"] * 4 + ["treatment"] * 4,
            "history": [10.0, 12.0, 8.0, 10.0, 100.0, 110.0, 90.0, 100.0],
        }
    )

    result = standardized_mean_differences(frame, "segment", ["history"], "control")

    assert result.iloc[0]["abs_smd"] > 0.1
    assert bool(result.iloc[0]["balanced"]) is False


@pytest.mark.parametrize("post_treatment", ["visit", "conversion", "spend"])
def test_post_treatment_covariates_are_prohibited(post_treatment: str) -> None:
    with pytest.raises(ValueError, match="post-treatment adjustment covariates"):
        validate_adjustment_covariates(["history", post_treatment])
