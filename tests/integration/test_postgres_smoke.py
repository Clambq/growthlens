from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from growthlens.data_contracts import HILLSTROM_CONTRACT
from growthlens.ingestion import load_dataset

POSTGRES_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.skipif(not POSTGRES_URL, reason="TEST_DATABASE_URL is not configured")
def test_postgres_audited_ingestion_smoke(tmp_path: Path) -> None:
    source = tmp_path / "hillstrom"
    source.mkdir()
    (source / "hillstrom.csv").write_text(
        "recency,history_segment,history,mens,womens,zip_code,newbie,channel,segment,visit,conversion,spend\n"
        "1,1) $0 - $100,50,1,0,Urban,1,Web,No E-Mail,0,0,0\n",
        encoding="utf-8",
    )
    engine = create_engine(POSTGRES_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        connection.execute(text("DROP SCHEMA IF EXISTS audit CASCADE"))

    manifest = load_dataset(engine, source, HILLSTROM_CONTRACT)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM raw.hillstrom")).scalar_one() == 1
        assert (
            connection.execute(text("SELECT status FROM audit.ingestion_runs")).scalar_one()
            == "succeeded"
        )
    assert manifest.files[0].rows_inserted == 1
