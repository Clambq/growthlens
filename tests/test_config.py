from pathlib import Path

import pytest

from growthlens.config import load_settings


def test_defaults_resolve_inside_repository() -> None:
    settings = load_settings({})
    repository_root = Path(__file__).resolve().parents[1]

    assert settings.database_url == "postgresql+psycopg://growthlens:growthlens@localhost:5432/growthlens"
    assert settings.raw_data_dir == repository_root / "data" / "raw"
    assert settings.artifact_dir == repository_root / "artifacts"


def test_windows_style_path_overrides_are_resolved() -> None:
    settings = load_settings(
        {
            "RAW_DATA_DIR": r"D:\analytics\raw",
            "ARTIFACT_DIR": r"D:\analytics\artifacts",
        }
    )

    assert settings.raw_data_dir == Path(r"D:\analytics\raw")
    assert settings.artifact_dir == Path(r"D:\analytics\artifacts")


def test_blank_database_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL cannot be blank"):
        load_settings({"DATABASE_URL": "   "})
