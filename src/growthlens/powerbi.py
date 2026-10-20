"""Deterministic, privacy-safe extracts for the Power BI semantic model."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ExportSpec:
    name: str
    filename: str
    grain: str
    keys: tuple[str, ...]
    source_relation: str


@dataclass(frozen=True)
class ExportedTable:
    name: str
    filename: str
    grain: str
    row_count: int
    sha256: str


EXPORT_SPECS = (
    ExportSpec(
        "customer_cohorts",
        "customer_cohorts.csv",
        "one row per acquisition cohort and activity month",
        ("cohort_month", "activity_month"),
        "mart_customer_cohorts",
    ),
    ExportSpec(
        "daily_kpis",
        "daily_kpis.csv",
        "one row per purchase date",
        ("metric_date",),
        "mart_daily_kpis",
    ),
    ExportSpec(
        "delivery_summary",
        "delivery_summary.csv",
        "one row per purchase date and delivery status",
        ("purchase_date", "is_late_delivery"),
        "mart_delivery_diagnostics",
    ),
    ExportSpec(
        "experiment_quality",
        "experiment_quality.csv",
        "one row per randomized segment",
        ("segment",),
        "mart_experiment_quality",
    ),
    ExportSpec(
        "experiment_summary",
        "experiment_summary.csv",
        "one row per randomized segment",
        ("segment",),
        "mart_experiment_summary",
    ),
    ExportSpec(
        "seller_scorecard",
        "seller_scorecard.csv",
        "one row per pseudonymous seller",
        ("seller_key",),
        "mart_seller_scorecard",
    ),
)

_FORBIDDEN_OUTPUT_COLUMNS = frozenset(
    {"customer_unique_id", "customer_id", "order_id", "seller_id"}
)


def _relation(name: str, schema: str | None) -> str:
    return f"{schema}.{name}" if schema else name


def _read_source(connection: Any, spec: ExportSpec, schema: str | None) -> pd.DataFrame:
    relation = _relation(spec.source_relation, schema)
    if spec.name == "customer_cohorts":
        query = f"""
            SELECT cohort_month, activity_month, month_offset,
                   COUNT(DISTINCT customer_unique_id) AS active_customers,
                   SUM(orders_in_month) AS orders,
                   SUM(merchandise_value) AS merchandise_value,
                   AVG(CAST(is_repeat_activity AS DOUBLE PRECISION)) AS repeat_activity_rate
            FROM {relation}
            GROUP BY cohort_month, activity_month, month_offset
        """
    elif spec.name == "delivery_summary":
        query = f"""
            SELECT purchase_date, is_late_delivery, COUNT(*) AS delivered_orders,
                   AVG(delivery_days) AS average_delivery_days,
                   AVG(delivery_delay_days) AS average_delivery_delay_days,
                   AVG(review_score) AS average_review_score,
                   SUM(merchandise_value) AS merchandise_value,
                   MAX(interpretation_label) AS interpretation_label
            FROM {relation}
            GROUP BY purchase_date, is_late_delivery
        """
    else:
        query = f"SELECT * FROM {relation}"
    frame = pd.read_sql_query(query, connection)
    if spec.name == "seller_scorecard":
        frame["seller_key"] = frame["seller_id"].astype(str).map(
            lambda value: "S-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        )
        frame = frame.drop(columns=["seller_id"])
    return frame


def _stable_csv(frame: pd.DataFrame, path: Path, keys: tuple[str, ...]) -> str:
    missing = set(keys).difference(frame.columns)
    if missing:
        raise ValueError(f"missing declared key columns: {sorted(missing)}")
    if frame.duplicated(list(keys)).any():
        raise ValueError(f"rows are not unique at declared key {keys}")
    forbidden = _FORBIDDEN_OUTPUT_COLUMNS.intersection(frame.columns)
    if forbidden:
        raise ValueError(f"forbidden identifier columns in BI export: {sorted(forbidden)}")
    ordered = frame.sort_values(list(keys), kind="mergesort").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered.to_csv(
        path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        date_format="%Y-%m-%d",
        float_format="%.10g",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_powerbi_inputs(
    connection: Any, output_dir: Path, *, schema: str | None = "marts"
) -> tuple[ExportedTable, ...]:
    """Export all declared dashboard tables at tested grains without raw entity IDs."""

    destination = Path(output_dir)
    exported: list[ExportedTable] = []
    for spec in EXPORT_SPECS:
        frame = _read_source(connection, spec, schema)
        output_path = destination / spec.filename
        digest = _stable_csv(frame, output_path, spec.keys)
        exported.append(
            ExportedTable(
                name=spec.name,
                filename=spec.filename,
                grain=spec.grain,
                row_count=len(frame),
                sha256=digest,
            )
        )
    return tuple(exported)
