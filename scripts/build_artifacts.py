"""Generate verified metrics and a run manifest from built warehouse relations."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime

import pandas as pd
from sqlalchemy import create_engine, text

from growthlens.config import load_settings
from growthlens.experimentation import holm_adjust, proportion_effect, sample_ratio_test
from growthlens.reporting import build_verified_metrics, write_verified_metrics


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main() -> int:
    settings = load_settings()
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        commerce = connection.execute(
            text(
                """
                SELECT COALESCE(SUM(orders), 0) AS orders,
                       COALESCE(SUM(merchandise_value), 0) AS merchandise_value,
                       CAST(SUM(on_time_delivery_orders) AS DOUBLE PRECISION)
                           / NULLIF(SUM(eligible_delivery_orders), 0)
                           AS on_time_delivery_rate,
                       CAST(SUM(review_score_total) AS DOUBLE PRECISION)
                           / NULLIF(SUM(reviewed_orders), 0)
                           AS average_review_score
                FROM marts.mart_daily_kpis
                """
            )
        ).mappings().one()
        experiment = pd.read_sql_query(
            text(
                """
                SELECT assignments.experiment_customer_id, assignments.segment,
                       outcomes.converted, outcomes.visited, outcomes.spend
                FROM marts.fct_experiment_assignments assignments
                JOIN marts.fct_experiment_outcomes outcomes USING (experiment_customer_id)
                """
            ),
            connection,
        )
        provenance_rows = connection.execute(
            text(
                """
                SELECT runs.dataset, runs.run_id, files.source_sha256
                FROM audit.ingestion_runs runs
                JOIN audit.ingestion_files files USING (run_id)
                WHERE runs.status = 'succeeded'
                  AND runs.finished_at = (
                    SELECT MAX(latest.finished_at) FROM audit.ingestion_runs latest
                    WHERE latest.dataset = runs.dataset AND latest.status = 'succeeded'
                  )
                ORDER BY runs.dataset, files.source_file
                """
            )
        ).mappings().all()

    source_provenance: dict[str, dict[str, object]] = {}
    for row in provenance_rows:
        entry = source_provenance.setdefault(
            row["dataset"], {"run_id": row["run_id"], "sha256": []}
        )
        entry["sha256"].append(row["source_sha256"])

    counts = experiment["segment"].value_counts().to_dict()
    srm = sample_ratio_test(counts, {group: 1 / 3 for group in counts})
    if not srm.passes:
        raise RuntimeError(f"experiment SRM gate failed: p={srm.p_value}")
    control = experiment.loc[experiment["segment"] == "No E-Mail", "converted"]
    treatment_names = ["Mens E-Mail", "Womens E-Mail"]
    effects = [
        proportion_effect(
            experiment.loc[experiment["segment"] == treatment, "converted"],
            control,
            treatment_name=treatment,
            control_name="No E-Mail",
        )
        for treatment in treatment_names
    ]
    adjusted = holm_adjust([effect.p_value for effect in effects])
    experiment_metrics = {
        "sample_ratio_p_value": {
            "value": srm.p_value,
            "analysis_type": "experiment_diagnostic",
        }
    }
    for effect, adjusted_p in zip(effects, adjusted, strict=True):
        key = effect.treatment_name.lower().replace(" ", "_").replace("-", "")
        experiment_metrics[f"{key}_conversion_effect"] = {
            "value": effect.absolute_effect,
            "analysis_type": "randomized_experiment",
            "confidence_interval": {
                "low": effect.ci_low,
                "high": effect.ci_high,
                "level": 0.95,
            },
            "raw_p_value": effect.p_value,
            "holm_adjusted_p_value": float(adjusted_p),
            "n_treatment": effect.n_treatment,
            "n_control": effect.n_control,
        }

    metrics = build_verified_metrics(
        source_provenance=source_provenance,
        observed_results={
            "commerce": {
                "orders": {"value": int(commerce["orders"]), "analysis_type": "descriptive"},
                "merchandise_value": {
                    "value": float(commerce["merchandise_value"]),
                    "analysis_type": "descriptive",
                },
                "on_time_delivery_rate": {
                    "value": float(commerce["on_time_delivery_rate"]),
                    "analysis_type": "associational",
                },
                "average_review_score": {
                    "value": float(commerce["average_review_score"]),
                    "analysis_type": "descriptive",
                },
            },
            "experiment": experiment_metrics,
        },
    )
    metrics_path = settings.artifact_dir / "verified_metrics.json"
    write_verified_metrics(metrics_path, metrics)
    metrics_hash = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_sha": _git_sha(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "verified_metrics_sha256": metrics_hash,
        "source_run_ids": {
            source: provenance["run_id"] for source, provenance in source_provenance.items()
        },
        "effect_methods": [asdict(effect)["method"] for effect in effects],
    }
    (settings.artifact_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(metrics_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
