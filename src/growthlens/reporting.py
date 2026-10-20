"""Deterministic, evidence-bearing analytics artifact generation."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
ALLOWED_ANALYSIS_TYPES = frozenset(
    {"descriptive", "associational", "experiment_diagnostic", "randomized_experiment"}
)


def _validate_json(value: object, path: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} must be a finite JSON number")
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string JSON key")
            _validate_json(item, f"{path}.{key}")
        return
    raise ValueError(f"{path} contains a non-JSON value: {type(value).__name__}")


def _validate_observed_results(results: Mapping[str, object]) -> None:
    for section, metrics in results.items():
        if section == "scenario_assumptions":
            raise ValueError("scenario assumptions must be separate from observed results")
        if not isinstance(metrics, Mapping):
            raise ValueError(f"observed_results.{section} must contain metric records")
        for metric_name, record in metrics.items():
            if metric_name == "scenario_assumptions":
                raise ValueError("scenario assumptions must be separate from observed results")
            if not isinstance(record, Mapping):
                raise ValueError(f"observed metric {section}.{metric_name} must be an object")
            analysis_type = record.get("analysis_type")
            if analysis_type not in ALLOWED_ANALYSIS_TYPES:
                raise ValueError(
                    f"observed metric {section}.{metric_name} requires a valid analysis_type"
                )
            if "value" not in record:
                raise ValueError(f"observed metric {section}.{metric_name} requires value")
            if analysis_type == "randomized_experiment" and "confidence_interval" not in record:
                raise ValueError(
                    f"randomized metric {section}.{metric_name} requires confidence_interval"
                )


def build_verified_metrics(
    *,
    source_provenance: Mapping[str, JSONValue],
    observed_results: Mapping[str, JSONValue],
    scenario_assumptions: Mapping[str, JSONValue] | None = None,
) -> dict[str, JSONValue]:
    """Build a deterministic evidence payload without wall-clock fields."""

    if not source_provenance:
        raise ValueError("source_provenance cannot be empty")
    for source, provenance in source_provenance.items():
        if not isinstance(provenance, Mapping) or not provenance.get("run_id"):
            raise ValueError(f"source {source} requires run_id provenance")
    _validate_observed_results(observed_results)
    payload: dict[str, JSONValue] = {
        "observed_results": deepcopy(dict(observed_results)),
        "scenario_assumptions": deepcopy(dict(scenario_assumptions or {})),
        "schema_version": "1.0.0",
        "source_provenance": deepcopy(dict(source_provenance)),
    }
    _validate_json(payload)
    return payload


def write_verified_metrics(path: Path, metrics: Mapping[str, JSONValue]) -> None:
    """Validate and atomically write stable, sorted UTF-8 JSON."""

    _validate_json(metrics)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    temporary.replace(destination)
