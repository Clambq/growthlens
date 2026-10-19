"""Transactional, audited, and idempotent raw CSV ingestion."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    exists,
    func,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.engine import Connection, Engine

from growthlens.data_contracts import DatasetContract, FileContract, verify_dataset

TABLE_MAPPINGS = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
    "hillstrom.csv": "hillstrom",
}


@dataclass(frozen=True, slots=True)
class LoadedFile:
    """Per-file result returned after a successful ingestion run."""

    source_file: str
    target_table: str
    source_sha256: str
    rows_read: int
    rows_inserted: int


@dataclass(frozen=True, slots=True)
class LoadManifest:
    """Successful ingestion evidence for one dataset attempt."""

    run_id: UUID
    dataset: str
    files: tuple[LoadedFile, ...]
    status: str


def _physical_table(engine: Engine, schema: str, name: str) -> tuple[str | None, str]:
    if engine.dialect.name == "postgresql":
        return schema, name
    return None, f"{schema}__{name}"


def _audit_tables(engine: Engine) -> tuple[Table, Table]:
    metadata = MetaData()
    schema, runs_name = _physical_table(engine, "audit", "ingestion_runs")
    _, files_name = _physical_table(engine, "audit", "ingestion_files")
    runs = Table(
        runs_name,
        metadata,
        Column("run_id", String(36), primary_key=True),
        Column("dataset", Text, nullable=False),
        Column("status", String(16), nullable=False),
        Column("started_at", DateTime(timezone=True), nullable=False),
        Column("finished_at", DateTime(timezone=True)),
        Column("error", Text),
        schema=schema,
    )
    files = Table(
        files_name,
        metadata,
        Column("file_id", Integer, primary_key=True, autoincrement=True),
        Column("run_id", String(36), nullable=False),
        Column("source_file", Text, nullable=False),
        Column("target_table", Text, nullable=False),
        Column("source_sha256", String(64), nullable=False),
        Column("rows_read", Integer, nullable=False),
        Column("rows_inserted", Integer, nullable=False),
        schema=schema,
    )
    return runs, files


def bootstrap_database(engine: Engine) -> None:
    """Create PostgreSQL schemas and portable audit tables if absent."""

    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
    runs, files = _audit_tables(engine)
    runs.metadata.create_all(engine, tables=[runs, files])


def _read_rows(path: Path, contract: FileContract) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open("r", encoding=contract.encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"{contract.name} row {row_number}: unexpected extra fields")
            missing_values = [name for name, value in row.items() if value is None]
            if missing_values:
                raise ValueError(
                    f"{contract.name} row {row_number}: missing fields {', '.join(missing_values)}"
                )
            rows.append({name: row[name] for name in fieldnames})
    return fieldnames, rows


def _raw_table(engine: Engine, logical_name: str, columns: tuple[str, ...]) -> Table:
    schema, table_name = _physical_table(engine, "raw", logical_name)
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        *(Column(name, Text) for name in columns),
        Column("_loaded_at", DateTime(timezone=True), nullable=False),
        Column("_source_file", Text, nullable=False),
        Column("_source_row_number", Integer, nullable=False),
        Column("_row_hash", String(64), primary_key=True),
        Column("_run_id", String(36), nullable=False),
        schema=schema,
    )


def _enrich_rows(
    rows: list[dict[str, str]],
    *,
    columns: tuple[str, ...],
    source_file: str,
    run_id: UUID,
    loaded_at: datetime,
) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for source_row_number, row in enumerate(rows, start=2):
        canonical = json.dumps(
            {name: row[name] for name in columns},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        row_hash = hashlib.sha256(
            f"{source_file}|{source_row_number}|{canonical}".encode()
        ).hexdigest()
        enriched.append(
            {
                **row,
                "_loaded_at": loaded_at,
                "_source_file": source_file,
                "_source_row_number": source_row_number,
                "_row_hash": row_hash,
                "_run_id": str(run_id),
            }
        )
    return enriched


def _load_file(
    connection: Connection,
    engine: Engine,
    *,
    run_id: UUID,
    loaded_at: datetime,
    path: Path,
    contract: FileContract,
    sha256: str,
) -> LoadedFile:
    logical_name = TABLE_MAPPINGS.get(contract.name)
    if logical_name is None:
        raise ValueError(f"no explicit table mapping for {contract.name}")
    columns, rows = _read_rows(path, contract)
    target = _raw_table(engine, logical_name, columns)
    target.create(connection, checkfirst=True)
    enriched = _enrich_rows(
        rows,
        columns=columns,
        source_file=contract.name,
        run_id=run_id,
        loaded_at=loaded_at,
    )

    before = int(connection.execute(select(func.count()).select_from(target)).scalar_one())
    if enriched:
        stage = Table(
            f"stage_{logical_name}_{run_id.hex[:8]}",
            MetaData(),
            *(Column(column.name, column.type) for column in target.columns),
            prefixes=["TEMPORARY"],
        )
        stage.create(connection)
        try:
            connection.execute(insert(stage), enriched)
            column_names = [column.name for column in target.columns]
            unseen_rows = select(*(stage.c[name] for name in column_names)).where(
                ~exists(
                    select(target.c["_row_hash"]).where(
                        target.c["_row_hash"] == stage.c["_row_hash"]
                    )
                )
            )
            connection.execute(insert(target).from_select(column_names, unseen_rows))
        finally:
            stage.drop(connection, checkfirst=True)
    after = int(connection.execute(select(func.count()).select_from(target)).scalar_one())
    return LoadedFile(
        source_file=contract.name,
        target_table=logical_name,
        source_sha256=sha256,
        rows_read=len(rows),
        rows_inserted=after - before,
    )


def load_dataset(engine: Engine, root: Path, contract: DatasetContract) -> LoadManifest:
    """Verify and load a complete dataset atomically, preserving an audit attempt."""

    bootstrap_database(engine)
    runs, audit_files = _audit_tables(engine)
    run_id = uuid4()
    started_at = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            insert(runs).values(
                run_id=str(run_id),
                dataset=contract.name,
                status="running",
                started_at=started_at,
            )
        )

    try:
        report = verify_dataset(Path(root), contract)
        if not report.ok:
            errors = [error for file in report.files for error in file.errors]
            raise ValueError("dataset verification failed: " + "; ".join(errors))
        checks = {file.name: file for file in report.files}
        loaded_at = datetime.now(UTC)
        loaded_files: list[LoadedFile] = []
        with engine.begin() as connection:
            for file_contract in contract.files:
                check = checks[file_contract.name]
                if check.sha256 is None:
                    raise ValueError(f"verified file has no hash: {file_contract.name}")
                loaded_file = _load_file(
                    connection,
                    engine,
                    run_id=run_id,
                    loaded_at=loaded_at,
                    path=check.path,
                    contract=file_contract,
                    sha256=check.sha256,
                )
                loaded_files.append(loaded_file)
                connection.execute(
                    insert(audit_files).values(
                        run_id=str(run_id),
                        source_file=loaded_file.source_file,
                        target_table=loaded_file.target_table,
                        source_sha256=loaded_file.source_sha256,
                        rows_read=loaded_file.rows_read,
                        rows_inserted=loaded_file.rows_inserted,
                    )
                )
            connection.execute(
                update(runs)
                .where(runs.c.run_id == str(run_id))
                .values(status="succeeded", finished_at=datetime.now(UTC))
            )
    except Exception as error:
        with engine.begin() as connection:
            connection.execute(
                update(runs)
                .where(runs.c.run_id == str(run_id))
                .values(
                    status="failed",
                    finished_at=datetime.now(UTC),
                    error=str(error),
                )
            )
        raise

    return LoadManifest(
        run_id=run_id,
        dataset=contract.name,
        files=tuple(loaded_files),
        status="succeeded",
    )


def engine_from_url(database_url: str) -> Engine:
    """Construct a future-style SQLAlchemy engine for CLI callers."""

    return create_engine(database_url)
