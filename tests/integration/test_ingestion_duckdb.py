from pathlib import Path

from sqlalchemy import create_engine, text

from growthlens.data_contracts import HILLSTROM_CONTRACT
from growthlens.ingestion import load_dataset


def test_duckdb_loader_uses_real_raw_and_audit_schemas(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "hillstrom.csv").write_text(
        "recency,history_segment,history,mens,womens,zip_code,newbie,channel,segment,visit,conversion,spend\n"
        "1,1) $0 - $100,50,1,0,Urban,1,Web,No E-Mail,0,0,0\n",
        encoding="utf-8",
    )
    engine = create_engine(f"duckdb:///{(tmp_path / 'warehouse.duckdb').as_posix()}")

    first = load_dataset(engine, source, HILLSTROM_CONTRACT)
    second = load_dataset(engine, source, HILLSTROM_CONTRACT)

    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from raw.hillstrom")).scalar_one() == 1
        assert (
            connection.execute(text("select count(*) from audit.ingestion_runs")).scalar_one()
            == 2
        )
    assert first.files[0].rows_inserted == 1
    assert second.files[0].rows_inserted == 0
