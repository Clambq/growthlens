from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import duckdb

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT = REPOSITORY_ROOT / "dbt"


def _run_dbt(database: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GROWTHLENS_DUCKDB_PATH"] = str(database)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "dbt.cli.main",
            "build",
            "--project-dir",
            str(DBT_PROJECT),
            "--profiles-dir",
            str(DBT_PROJECT),
            "--target",
            "duckdb",
            "--no-use-colors",
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _create_metric_fixture(database: Path) -> None:
    connection = duckdb.connect(str(database))
    try:
        connection.execute("CREATE SCHEMA raw")
        statements = [
            """
            CREATE TABLE raw.customers AS SELECT * FROM (VALUES
              ('customer-order-1', 'person-1', '01000', 'sao paulo', 'SP', TIMESTAMP '2024-01-01'),
              ('customer-order-2', 'person-1', '01000', 'sao paulo', 'SP', TIMESTAMP '2024-01-01'),
              ('customer-order-3', 'person-2', '20000', 'rio de janeiro', 'RJ', TIMESTAMP '2024-01-01')
            ) t(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city,
                customer_state, _loaded_at)
            """,
            """
            CREATE TABLE raw.geolocation AS SELECT * FROM (VALUES
              ('01000', '-23.55', '-46.63', 'sao paulo', 'SP', TIMESTAMP '2024-01-01')
            ) t(geolocation_zip_code_prefix, geolocation_lat, geolocation_lng,
                geolocation_city, geolocation_state, _loaded_at)
            """,
            """
            CREATE TABLE raw.products AS SELECT * FROM (VALUES
              ('product-1', 'beleza_saude', '10', '50', '1', '500', '10', '5', '8', TIMESTAMP '2024-01-01'),
              ('product-2', 'beleza_saude', '10', '50', '1', '700', '12', '6', '9', TIMESTAMP '2024-01-01')
            ) t(product_id, product_category_name, product_name_lenght,
                product_description_lenght, product_photos_qty, product_weight_g,
                product_length_cm, product_height_cm, product_width_cm, _loaded_at)
            """,
            """
            CREATE TABLE raw.sellers AS SELECT * FROM (VALUES
              ('seller-1', '01000', 'sao paulo', 'SP', TIMESTAMP '2024-01-01')
            ) t(seller_id, seller_zip_code_prefix, seller_city, seller_state, _loaded_at)
            """,
            """
            CREATE TABLE raw.category_translation AS SELECT * FROM (VALUES
              ('beleza_saude', 'health_beauty', TIMESTAMP '2024-01-01')
            ) t(product_category_name, product_category_name_english, _loaded_at)
            """,
            """
            CREATE TABLE raw.orders AS SELECT * FROM (VALUES
              ('order-1', 'customer-order-1', 'delivered', '2018-01-01 10:00:00',
               '2018-01-01 11:00:00', '2018-01-02 09:00:00', '2018-01-05 12:00:00',
               '2018-01-10 00:00:00', TIMESTAMP '2024-01-01'),
              ('order-2', 'customer-order-2', 'delivered', '2018-01-02 10:00:00',
               '2018-01-02 11:00:00', '2018-01-03 09:00:00', '2018-01-12 12:00:00',
               '2018-01-10 00:00:00', TIMESTAMP '2024-01-01'),
              ('order-3', 'customer-order-3', 'canceled', '2018-01-02 12:00:00',
               NULL, NULL, NULL, '2018-01-15 00:00:00', TIMESTAMP '2024-01-01')
            ) t(order_id, customer_id, order_status, order_purchase_timestamp,
                order_approved_at, order_delivered_carrier_date,
                order_delivered_customer_date, order_estimated_delivery_date, _loaded_at)
            """,
            """
            CREATE TABLE raw.order_items AS SELECT * FROM (VALUES
              ('order-1', '1', 'product-1', 'seller-1', '2018-01-03', '100.00', '10.00', TIMESTAMP '2024-01-01'),
              ('order-1', '2', 'product-2', 'seller-1', '2018-01-03', '50.00', '5.00', TIMESTAMP '2024-01-01'),
              ('order-2', '1', 'product-1', 'seller-1', '2018-01-04', '50.00', '5.00', TIMESTAMP '2024-01-01'),
              ('order-3', '1', 'product-2', 'seller-1', '2018-01-04', '200.00', '20.00', TIMESTAMP '2024-01-01')
            ) t(order_id, order_item_id, product_id, seller_id, shipping_limit_date,
                price, freight_value, _loaded_at)
            """,
            """
            CREATE TABLE raw.order_payments AS SELECT * FROM (VALUES
              ('order-1', '1', 'credit_card', '1', '100.00', TIMESTAMP '2024-01-01'),
              ('order-1', '2', 'voucher', '1', '65.00', TIMESTAMP '2024-01-01'),
              ('order-2', '1', 'credit_card', '1', '55.00', TIMESTAMP '2024-01-01'),
              ('order-3', '1', 'credit_card', '1', '220.00', TIMESTAMP '2024-01-01')
            ) t(order_id, payment_sequential, payment_type, payment_installments,
                payment_value, _loaded_at)
            """,
            """
            CREATE TABLE raw.order_reviews AS SELECT * FROM (VALUES
              ('review-1', 'order-1', '5', NULL, NULL, '2018-01-06', '2018-01-06 12:00:00', TIMESTAMP '2024-01-01'),
              ('review-2', 'order-1', '3', NULL, NULL, '2018-01-06', '2018-01-07 12:00:00', TIMESTAMP '2024-01-01'),
              ('review-3', 'order-2', '2', NULL, NULL, '2018-01-13', '2018-01-13 12:00:00', TIMESTAMP '2024-01-01'),
              ('review-4', 'order-3', '1', NULL, NULL, '2018-01-03', '2018-01-03 12:00:00', TIMESTAMP '2024-01-01')
            ) t(review_id, order_id, review_score, review_comment_title,
                review_comment_message, review_creation_date, review_answer_timestamp, _loaded_at)
            """,
            """
            CREATE TABLE raw.hillstrom AS SELECT * FROM (VALUES
              ('2', '2) $100 - $200', '150.00', '1', '0', 'Urban', '0', 'Web',
               'Mens E-Mail', '1', '1', '25.00', TIMESTAMP '2024-01-01')
            ) t(recency, history_segment, history, mens, womens, zip_code, newbie,
                channel, segment, visit, "conversion", spend, _loaded_at)
            """,
        ]
        for statement in statements:
            connection.execute(statement)
    finally:
        connection.close()


def test_order_and_daily_metrics_reconcile_without_fanout(tmp_path: Path) -> None:
    database = tmp_path / "commerce.duckdb"
    _create_metric_fixture(database)

    result = _run_dbt(database)

    assert result.returncode == 0, result.stdout + result.stderr
    connection = duckdb.connect(str(database))
    try:
        order = connection.execute(
            """
            SELECT merchandise_value, freight_value, payment_value, review_score,
                   item_count, payment_count, review_count
            FROM marts.fct_orders WHERE order_id = 'order-1'
            """
        ).fetchone()
        daily = connection.execute(
            """
            SELECT metric_date, merchandise_value, freight_value, payment_value,
                   orders, customers, average_order_value, repeat_customer_rate,
                   on_time_delivery_rate, average_review_score
            FROM marts.mart_daily_kpis ORDER BY metric_date
            """
        ).fetchall()
    finally:
        connection.close()

    assert order == (
        Decimal("150.00"),
        Decimal("15.00"),
        Decimal("165.00"),
        4.0,
        2,
        2,
        2,
    )
    assert daily == [
        (
            daily[0][0],
            Decimal("150.00"),
            Decimal("15.00"),
            Decimal("165.00"),
            1,
            1,
            150.0,
            0.0,
            1.0,
            4.0,
        ),
        (
            daily[1][0],
            Decimal("50.00"),
            Decimal("5.00"),
            Decimal("55.00"),
            1,
            1,
            50.0,
            1.0,
            0.0,
            2.0,
        ),
    ]


def test_canceled_orders_remain_auditable_but_do_not_enter_daily_kpis(tmp_path: Path) -> None:
    database = tmp_path / "scope.duckdb"
    _create_metric_fixture(database)
    result = _run_dbt(database)
    assert result.returncode == 0, result.stdout + result.stderr

    connection = duckdb.connect(str(database))
    try:
        canceled = connection.execute(
            """
            SELECT is_commercial_order, merchandise_value, payment_value
            FROM marts.fct_orders WHERE order_id = 'order-3'
            """
        ).fetchone()
        daily_merchandise = connection.execute(
            "SELECT SUM(merchandise_value) FROM marts.mart_daily_kpis"
        ).fetchone()
    finally:
        connection.close()

    assert canceled == (False, Decimal("200.00"), Decimal("220.00"))
    assert daily_merchandise == (Decimal("200.00"),)
