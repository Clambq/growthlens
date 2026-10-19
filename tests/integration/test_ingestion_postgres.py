from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from growthlens.data_contracts import HILLSTROM_CONTRACT, OLIST_CONTRACT
from growthlens.ingestion import load_dataset


@pytest.fixture
def engine() -> Engine:
    return create_engine("sqlite+pysqlite:///:memory:")


def _write_contract_fixture(root: Path, contract: object, rows: int = 1) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for file_contract in contract.files:  # type: ignore[attr-defined]
        columns = sorted(file_contract.required_columns)
        values = [f"value_{index}" for index in range(len(columns))]
        body = [",".join(columns)]
        body.extend(",".join(values) for _ in range(rows))
        (root / file_contract.name).write_bytes(("\n".join(body) + "\n").encode("utf-8"))


def _scalar(engine: Engine, statement: str) -> int:
    with engine.connect() as connection:
        return int(connection.execute(text(statement)).scalar_one())


def test_first_hillstrom_load_records_rows_and_audit_metadata(
    engine: Engine, tmp_path: Path
) -> None:
    root = tmp_path / "hillstrom"
    _write_contract_fixture(root, HILLSTROM_CONTRACT, rows=2)

    manifest = load_dataset(engine, root, HILLSTROM_CONTRACT)

    assert manifest.dataset == "hillstrom"
    assert manifest.status == "succeeded"
    assert manifest.files[0].rows_read == 2
    assert manifest.files[0].rows_inserted == 2
    assert _scalar(engine, 'SELECT COUNT(*) FROM "raw__hillstrom"') == 2
    assert _scalar(engine, 'SELECT COUNT(*) FROM "audit__ingestion_runs"') == 1
    assert _scalar(engine, 'SELECT COUNT(*) FROM "audit__ingestion_files"') == 1
    with engine.connect() as connection:
        metadata = connection.execute(
            text(
                'SELECT "_source_file", "_row_hash", "_run_id", "_loaded_at" '
                'FROM "raw__hillstrom" LIMIT 1'
            )
        ).mappings().one()
    assert metadata["_source_file"] == "hillstrom.csv"
    assert len(metadata["_row_hash"]) == 64
    assert metadata["_run_id"] == str(manifest.run_id)
    assert metadata["_loaded_at"] is not None


def test_identical_second_load_adds_audit_without_duplicate_business_rows(
    engine: Engine, tmp_path: Path
) -> None:
    root = tmp_path / "hillstrom"
    _write_contract_fixture(root, HILLSTROM_CONTRACT, rows=2)

    first = load_dataset(engine, root, HILLSTROM_CONTRACT)
    second = load_dataset(engine, root, HILLSTROM_CONTRACT)

    assert first.files[0].rows_inserted == 2
    assert second.files[0].rows_read == 2
    assert second.files[0].rows_inserted == 0
    assert _scalar(engine, 'SELECT COUNT(*) FROM "raw__hillstrom"') == 2
    assert _scalar(engine, 'SELECT COUNT(*) FROM "audit__ingestion_runs"') == 2


def test_bad_csv_row_rolls_back_business_rows_and_records_failed_attempt(
    engine: Engine, tmp_path: Path
) -> None:
    root = tmp_path / "hillstrom"
    _write_contract_fixture(root, HILLSTROM_CONTRACT, rows=1)
    load_dataset(engine, root, HILLSTROM_CONTRACT)
    columns = sorted(HILLSTROM_CONTRACT.files[0].required_columns)
    (root / "hillstrom.csv").write_bytes(
        ((",".join(columns) + "\n") + ",".join(["x"] * (len(columns) + 1)) + "\n").encode()
    )

    with pytest.raises(ValueError, match="unexpected extra fields"):
        load_dataset(engine, root, HILLSTROM_CONTRACT)

    assert _scalar(engine, 'SELECT COUNT(*) FROM "raw__hillstrom"') == 1
    assert _scalar(engine, 'SELECT COUNT(*) FROM "audit__ingestion_runs"') == 2
    assert _scalar(
        engine,
        'SELECT COUNT(*) FROM "audit__ingestion_runs" WHERE status = \'failed\'',
    ) == 1


def test_minimal_olist_manifest_loads_each_file_once(engine: Engine, tmp_path: Path) -> None:
    root = tmp_path / "olist"
    _write_contract_fixture(root, OLIST_CONTRACT)

    manifest = load_dataset(engine, root, OLIST_CONTRACT)

    assert len(manifest.files) == 9
    assert sum(file.rows_inserted for file in manifest.files) == 9
    assert _scalar(engine, 'SELECT COUNT(*) FROM "raw__orders"') == 1
    assert _scalar(engine, 'SELECT COUNT(*) FROM "audit__ingestion_files"') == 9
