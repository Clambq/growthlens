from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from growthlens.powerbi import EXPORT_SPECS, export_powerbi_inputs

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def dashboard_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    pd.DataFrame(
        [
            {
                "metric_date": "2024-01-02",
                "merchandise_value": 120.0,
                "freight_value": 12.0,
                "payment_value": 132.0,
                "orders": 2,
                "customers": 2,
                "average_order_value": 60.0,
                "repeat_customer_rate": 0.5,
                "on_time_delivery_rate": 1.0,
                "average_review_score": 4.5,
            },
            {
                "metric_date": "2024-01-01",
                "merchandise_value": 80.0,
                "freight_value": 8.0,
                "payment_value": 88.0,
                "orders": 1,
                "customers": 1,
                "average_order_value": 80.0,
                "repeat_customer_rate": 0.0,
                "on_time_delivery_rate": 0.0,
                "average_review_score": 2.0,
            },
        ]
    ).to_sql("mart_daily_kpis", connection, index=False)
    pd.DataFrame(
        [
            {
                "cohort_month": "2024-01-01",
                "activity_month": "2024-01-01",
                "month_offset": 0,
                "customer_unique_id": "private-customer-1",
                "orders_in_month": 1,
                "merchandise_value": 80.0,
                "is_repeat_activity": 0,
            },
            {
                "cohort_month": "2024-01-01",
                "activity_month": "2024-02-01",
                "month_offset": 1,
                "customer_unique_id": "private-customer-1",
                "orders_in_month": 2,
                "merchandise_value": 120.0,
                "is_repeat_activity": 1,
            },
        ]
    ).to_sql("mart_customer_cohorts", connection, index=False)
    pd.DataFrame(
        [
            {
                "seller_id": "raw-seller-1",
                "commercial_order_count": 3,
                "merchandise_value": 200.0,
                "freight_value": 20.0,
                "late_delivery_rate": 1 / 3,
                "average_review_score": 4.0,
                "is_priority_eligible": 1,
                "priority_score": 0.28,
            }
        ]
    ).to_sql("mart_seller_scorecard", connection, index=False)
    pd.DataFrame(
        [
            {
                "order_id": "private-order-1",
                "customer_unique_id": "private-customer-1",
                "purchase_date": "2024-01-01",
                "delivery_days": 5,
                "delivery_delay_days": -2,
                "is_late_delivery": 0,
                "review_score": 5,
                "merchandise_value": 80.0,
                "interpretation_label": "associational_not_causal",
            }
        ]
    ).to_sql("mart_delivery_diagnostics", connection, index=False)
    pd.DataFrame(
        [
            {
                "segment": "No E-Mail",
                "customers": 100,
                "visit_rate": 0.20,
                "conversion_rate": 0.05,
                "average_spend": 1.5,
                "total_spend": 150.0,
            },
            {
                "segment": "Mens E-Mail",
                "customers": 100,
                "visit_rate": 0.25,
                "conversion_rate": 0.08,
                "average_spend": 2.2,
                "total_spend": 220.0,
            },
        ]
    ).to_sql("mart_experiment_summary", connection, index=False)
    pd.DataFrame(
        [
            {
                "segment": "No E-Mail",
                "observed_count": 100,
                "observed_share": 0.5,
                "duplicate_customer_count": 0,
            },
            {
                "segment": "Mens E-Mail",
                "observed_count": 100,
                "observed_share": 0.5,
                "duplicate_customer_count": 0,
            },
        ]
    ).to_sql("mart_experiment_quality", connection, index=False)
    yield connection
    connection.close()


def test_every_dashboard_export_declares_grain_key_and_stable_filename() -> None:
    filenames = [spec.filename for spec in EXPORT_SPECS]

    assert len(EXPORT_SPECS) == 6
    assert len(filenames) == len(set(filenames))
    assert filenames == sorted(filenames)
    for spec in EXPORT_SPECS:
        assert spec.grain
        assert spec.keys
        assert spec.filename.endswith(".csv")


def test_exports_reconcile_fixture_values_and_are_deterministic(
    dashboard_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    first = export_powerbi_inputs(dashboard_connection, tmp_path / "first", schema=None)
    second = export_powerbi_inputs(dashboard_connection, tmp_path / "second", schema=None)

    assert [item.filename for item in first] == [spec.filename for spec in EXPORT_SPECS]
    assert [(item.filename, item.sha256) for item in first] == [
        (item.filename, item.sha256) for item in second
    ]
    daily = pd.read_csv(tmp_path / "first" / "daily_kpis.csv")
    assert daily["metric_date"].tolist() == ["2024-01-01", "2024-01-02"]
    assert daily["merchandise_value"].sum() == pytest.approx(200.0)
    assert daily["orders"].sum() == 3
    cohort = pd.read_csv(tmp_path / "first" / "customer_cohorts.csv")
    assert cohort.loc[cohort["month_offset"] == 1, "active_customers"].item() == 1


def test_no_raw_customer_order_or_seller_identifiers_enter_bi_layer(
    dashboard_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    export_powerbi_inputs(dashboard_connection, tmp_path, schema=None)
    forbidden = {"customer_unique_id", "customer_id", "order_id", "seller_id"}

    for path in tmp_path.glob("*.csv"):
        with path.open(encoding="utf-8", newline="") as stream:
            header = set(next(csv.reader(stream)))
        assert header.isdisjoint(forbidden), path.name


def test_duplicate_declared_key_fails_export(
    dashboard_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    dashboard_connection.execute(
        "INSERT INTO mart_daily_kpis SELECT * FROM mart_daily_kpis LIMIT 1"
    )

    with pytest.raises(ValueError, match="declared key"):
        export_powerbi_inputs(dashboard_connection, tmp_path, schema=None)


def test_version_controlled_powerbi_project_declares_five_decision_pages() -> None:
    page_root = PROJECT_ROOT / "powerbi" / "GrowthLens.Report" / "definition" / "pages"
    metadata = json.loads((page_root / "pages.json").read_text(encoding="utf-8"))
    names = [
        json.loads((page_root / page / "page.json").read_text(encoding="utf-8"))[
            "displayName"
        ]
        for page in metadata["pageOrder"]
    ]

    assert names == [
        "Management Overview",
        "Revenue and Customer Growth",
        "Fulfillment and Seller Operations",
        "Experiment Decision",
        "Data Quality",
    ]
    assert (PROJECT_ROOT / "powerbi" / "GrowthLens.pbip").is_file()
    assert (PROJECT_ROOT / "powerbi" / "GrowthLens.SemanticModel" / "definition.pbism").is_file()
