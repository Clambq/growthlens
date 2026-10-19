from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import duckdb

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT = REPOSITORY_ROOT / "dbt"


def _create_raw_fixture(database: Path, *, order_status: str = "delivered") -> None:
    connection = duckdb.connect(str(database))
    try:
        connection.execute("CREATE SCHEMA raw")
        statements = [
            """
            CREATE TABLE raw.customers AS SELECT
              'customer-order-1' customer_id, 'customer-person-1' customer_unique_id,
              '01000' customer_zip_code_prefix, 'sao paulo' customer_city,
              'SP' customer_state, TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.geolocation AS SELECT
              '01000' geolocation_zip_code_prefix, '-23.55' geolocation_lat,
              '-46.63' geolocation_lng, 'sao paulo' geolocation_city,
              'SP' geolocation_state, TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.products AS SELECT
              'product-1' product_id, 'beleza_saude' product_category_name,
              '10' product_name_lenght, '50' product_description_lenght,
              '1' product_photos_qty, '500' product_weight_g, '10' product_length_cm,
              '5' product_height_cm, '8' product_width_cm,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.sellers AS SELECT
              'seller-1' seller_id, '01000' seller_zip_code_prefix,
              'sao paulo' seller_city, 'SP' seller_state,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.category_translation AS SELECT
              'beleza_saude' product_category_name, 'health_beauty' product_category_name_english,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            f"""
            CREATE TABLE raw.orders AS SELECT
              'order-1' order_id, 'customer-order-1' customer_id,
              '{order_status}' order_status,
              '2018-01-01 10:00:00' order_purchase_timestamp,
              '2018-01-01 11:00:00' order_approved_at,
              '2018-01-02 09:00:00' order_delivered_carrier_date,
              '2018-01-05 12:00:00' order_delivered_customer_date,
              '2018-01-10 00:00:00' order_estimated_delivery_date,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.order_items AS SELECT
              'order-1' order_id, '1' order_item_id, 'product-1' product_id,
              'seller-1' seller_id, '2018-01-03 00:00:00' shipping_limit_date,
              '100.00' price, '10.00' freight_value,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.order_payments AS SELECT
              'order-1' order_id, '1' payment_sequential, 'credit_card' payment_type,
              '1' payment_installments, '110.00' payment_value,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.order_reviews AS SELECT
              'review-1' review_id, 'order-1' order_id, '5' review_score,
              NULL::VARCHAR review_comment_title, NULL::VARCHAR review_comment_message,
              '2018-01-06 00:00:00' review_creation_date,
              '2018-01-06 12:00:00' review_answer_timestamp,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
            """
            CREATE TABLE raw.hillstrom AS SELECT
              '2' recency, '2) $100 - $200' history_segment, '150.00' history,
              '1' mens, '0' womens, 'Urban' zip_code, '0' newbie,
              'Web' channel, 'Mens E-Mail' segment, '1' visit,
              '1' "conversion", '25.00' spend,
              TIMESTAMP '2024-01-01' _loaded_at
            """,
        ]
        for statement in statements:
            connection.execute(statement)
    finally:
        connection.close()


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


def test_staging_build_exposes_typed_relations_and_customer_semantics(tmp_path: Path) -> None:
    assert (DBT_PROJECT / "dbt_project.yml").is_file()
    database = tmp_path / "warehouse.duckdb"
    _create_raw_fixture(database)

    result = _run_dbt(database)

    assert result.returncode == 0, result.stdout + result.stderr
    connection = duckdb.connect(str(database))
    try:
        order = connection.execute(
            """
            SELECT order_status, purchased_at, has_invalid_timestamp_order
            FROM staging.stg_olist_orders
            """
        ).fetchone()
        customer_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE staging.stg_olist_customers"
            ).fetchall()
        }
        segment = connection.execute(
            "SELECT segment FROM staging.stg_hillstrom_customers"
        ).fetchone()
    finally:
        connection.close()

    assert order is not None
    assert order[0] == "delivered"
    assert str(order[1]) == "2018-01-01 10:00:00"
    assert order[2] is False
    assert {"customer_order_id", "customer_unique_id"} <= customer_columns
    assert segment == ("Mens E-Mail",)


def test_invalid_order_status_causes_dbt_build_to_fail(tmp_path: Path) -> None:
    database = tmp_path / "broken.duckdb"
    _create_raw_fixture(database, order_status="invented_status")

    result = _run_dbt(database)

    assert result.returncode != 0
    assert "accepted_values" in (result.stdout + result.stderr)
