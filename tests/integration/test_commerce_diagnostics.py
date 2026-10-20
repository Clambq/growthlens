from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import duckdb

from tests.integration.test_commerce_metrics import _create_metric_fixture, _run_dbt


def _extend_diagnostic_fixture(database: Path) -> None:
    connection = duckdb.connect(str(database))
    try:
        connection.execute(
            """
            INSERT INTO raw.customers VALUES
              ('customer-order-4', 'person-1', '01000', 'sao paulo', 'SP', TIMESTAMP '2024-01-01'),
              ('customer-order-5', 'person-3', '30000', 'belo horizonte', 'MG', TIMESTAMP '2024-01-01'),
              ('customer-order-6', 'person-4', '40000', 'salvador', 'BA', TIMESTAMP '2024-01-01')
            """
        )
        connection.execute(
            """
            INSERT INTO raw.sellers VALUES
              ('seller-2', '40000', 'salvador', 'BA', TIMESTAMP '2024-01-01')
            """
        )
        connection.execute(
            """
            INSERT INTO raw.orders VALUES
              ('order-4', 'customer-order-4', 'delivered', '2018-02-01 10:00:00',
               '2018-02-01 11:00:00', '2018-02-02 09:00:00', '2018-02-05 12:00:00',
               '2018-02-10 00:00:00', TIMESTAMP '2024-01-01'),
              ('order-5', 'customer-order-5', 'delivered', '2018-06-01 10:00:00',
               '2018-06-01 11:00:00', '2018-06-02 09:00:00', '2018-06-05 12:00:00',
               '2018-06-10 00:00:00', TIMESTAMP '2024-01-01'),
              ('order-6', 'customer-order-6', 'delivered', '2018-06-01 12:00:00',
               '2018-06-01 13:00:00', '2018-06-03 09:00:00', '2018-06-12 12:00:00',
               '2018-06-10 00:00:00', TIMESTAMP '2024-01-01')
            """
        )
        connection.execute(
            """
            INSERT INTO raw.order_items VALUES
              ('order-4', '1', 'product-1', 'seller-1', '2018-02-03', '20.00', '2.00', TIMESTAMP '2024-01-01'),
              ('order-5', '1', 'product-2', 'seller-1', '2018-06-03', '1000.00', '20.00', TIMESTAMP '2024-01-01'),
              ('order-6', '1', 'product-2', 'seller-2', '2018-06-04', '80.00', '8.00', TIMESTAMP '2024-01-01')
            """
        )
        connection.execute(
            """
            INSERT INTO raw.order_payments VALUES
              ('order-4', '1', 'credit_card', '1', '22.00', TIMESTAMP '2024-01-01'),
              ('order-5', '1', 'credit_card', '1', '1020.00', TIMESTAMP '2024-01-01'),
              ('order-6', '1', 'credit_card', '1', '88.00', TIMESTAMP '2024-01-01')
            """
        )
        connection.execute(
            """
            INSERT INTO raw.order_reviews VALUES
              ('review-5', 'order-4', '5', NULL, NULL, '2018-02-06', '2018-02-06 12:00:00', TIMESTAMP '2024-01-01'),
              ('review-6', 'order-5', '5', NULL, NULL, '2018-06-06', '2018-06-06 12:00:00', TIMESTAMP '2024-01-01'),
              ('review-7', 'order-6', '1', NULL, NULL, '2018-06-13', '2018-06-13 12:00:00', TIMESTAMP '2024-01-01')
            """
        )
    finally:
        connection.close()


def test_cohort_assignment_offsets_and_repeat_activity(tmp_path: Path) -> None:
    database = tmp_path / "cohorts.duckdb"
    _create_metric_fixture(database)
    _extend_diagnostic_fixture(database)
    result = _run_dbt(database)
    assert result.returncode == 0, result.stdout + result.stderr

    connection = duckdb.connect(str(database))
    try:
        rows = connection.execute(
            """
            SELECT cohort_month, activity_month, month_offset, orders_in_month,
                   is_repeat_activity
            FROM marts.mart_customer_cohorts
            WHERE customer_unique_id = 'person-1'
            ORDER BY activity_month
            """
        ).fetchall()
    finally:
        connection.close()

    assert [row[2:] for row in rows] == [(0, 2, False), (1, 1, True)]
    assert rows[0][0] == rows[0][1]


def test_rfm_uses_documented_fixed_boundaries(tmp_path: Path) -> None:
    database = tmp_path / "rfm.duckdb"
    _create_metric_fixture(database)
    _extend_diagnostic_fixture(database)
    result = _run_dbt(database)
    assert result.returncode == 0, result.stdout + result.stderr

    connection = duckdb.connect(str(database))
    try:
        scores = dict(
            connection.execute(
                """
                SELECT customer_unique_id,
                       (recency_score, frequency_score, monetary_score)
                FROM marts.mart_customer_rfm
                WHERE customer_unique_id IN ('person-1', 'person-3')
                """
            ).fetchall()
        )
    finally:
        connection.close()

    assert scores["person-1"] == (2, 3, 2)
    assert scores["person-3"] == (5, 1, 5)


def test_seller_minimum_volume_and_delivery_association_labels(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    _create_metric_fixture(database)
    _extend_diagnostic_fixture(database)
    result = _run_dbt(database)
    assert result.returncode == 0, result.stdout + result.stderr

    connection = duckdb.connect(str(database))
    try:
        sellers = dict(
            connection.execute(
                """
                SELECT seller_id, is_priority_eligible
                FROM marts.mart_seller_scorecard
                WHERE seller_id IN ('seller-1', 'seller-2')
                """
            ).fetchall()
        )
        early = connection.execute(
            """
            SELECT delivery_delay_days, interpretation_label, review_score
            FROM marts.mart_delivery_diagnostics WHERE order_id = 'order-1'
            """
        ).fetchone()
        late = connection.execute(
            """
            SELECT delivery_delay_days FROM marts.mart_delivery_diagnostics
            WHERE order_id = 'order-6'
            """
        ).fetchone()
    finally:
        connection.close()

    assert sellers == {"seller-1": True, "seller-2": False}
    assert early == (-5, "associational_not_causal", 4.0)
    assert late == (2,)


def test_seller_scorecard_keeps_commercial_value_at_item_grain(tmp_path: Path) -> None:
    database = tmp_path / "seller-value.duckdb"
    _create_metric_fixture(database)
    _extend_diagnostic_fixture(database)
    result = _run_dbt(database)
    assert result.returncode == 0, result.stdout + result.stderr

    connection = duckdb.connect(str(database))
    try:
        seller_value = connection.execute(
            """
            SELECT merchandise_value FROM marts.mart_seller_scorecard
            WHERE seller_id = 'seller-1'
            """
        ).fetchone()
    finally:
        connection.close()

    assert seller_value == (Decimal("1220.00"),)
