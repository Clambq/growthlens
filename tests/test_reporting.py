import hashlib
import json
from pathlib import Path

import pytest

from growthlens.reporting import build_verified_metrics, write_verified_metrics


def _valid_payload() -> dict[str, object]:
    return build_verified_metrics(
        source_provenance={
            "olist": {"run_id": "run-commerce-1", "sha256": ["abc123"]},
            "hillstrom": {"run_id": "run-experiment-1", "sha256": ["def456"]},
        },
        observed_results={
            "commerce": {
                "orders": {"value": 2, "analysis_type": "descriptive"},
            },
            "experiment": {
                "mens_conversion_effect": {
                    "value": 0.012,
                    "analysis_type": "randomized_experiment",
                    "confidence_interval": {"low": 0.004, "high": 0.020, "level": 0.95},
                }
            },
        },
        scenario_assumptions={"annualization_days": 365},
    )


def test_verified_metrics_has_schema_provenance_and_separate_scenarios() -> None:
    payload = _valid_payload()

    assert payload["schema_version"] == "1.0.0"
    assert payload["source_provenance"]["olist"]["run_id"] == "run-commerce-1"
    assert payload["observed_results"]["commerce"]["orders"]["analysis_type"] == "descriptive"
    assert payload["observed_results"]["experiment"]["mens_conversion_effect"][
        "confidence_interval"
    ] == {"low": 0.004, "high": 0.02, "level": 0.95}
    assert payload["scenario_assumptions"] == {"annualization_days": 365}


def test_json_output_is_stably_ordered_and_repeatable(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    payload = _valid_payload()

    write_verified_metrics(first, payload)
    write_verified_metrics(second, dict(reversed(list(payload.items()))))

    assert first.read_bytes() == second.read_bytes()
    assert hashlib.sha256(first.read_bytes()).hexdigest() == hashlib.sha256(
        second.read_bytes()
    ).hexdigest()
    assert list(json.loads(first.read_text(encoding="utf-8"))) == sorted(payload)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_are_rejected(invalid: float) -> None:
    with pytest.raises(ValueError, match="finite JSON number"):
        build_verified_metrics(
            source_provenance={"source": {"run_id": "run-1"}},
            observed_results={
                "commerce": {
                    "orders": {"value": invalid, "analysis_type": "descriptive"},
                }
            },
        )


def test_observed_result_requires_explicit_analysis_type() -> None:
    with pytest.raises(ValueError, match="analysis_type"):
        build_verified_metrics(
            source_provenance={"source": {"run_id": "run-1"}},
            observed_results={"commerce": {"orders": {"value": 2}}},
        )


def test_randomized_effect_requires_confidence_interval() -> None:
    with pytest.raises(ValueError, match="confidence_interval"):
        build_verified_metrics(
            source_provenance={"source": {"run_id": "run-1"}},
            observed_results={
                "experiment": {
                    "effect": {"value": 0.1, "analysis_type": "randomized_experiment"}
                }
            },
        )


def test_scenario_assumptions_cannot_be_nested_in_observed_results() -> None:
    with pytest.raises(ValueError, match="scenario assumptions must be separate"):
        build_verified_metrics(
            source_provenance={"source": {"run_id": "run-1"}},
            observed_results={
                "commerce": {
                    "scenario_assumptions": {
                        "value": 365,
                        "analysis_type": "descriptive",
                    }
                }
            },
        )
