"""Runtime configuration with repository-relative defaults."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://growthlens:growthlens@localhost:5432/growthlens"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated paths and connection settings used by every pipeline stage."""

    database_url: str
    raw_data_dir: Path
    artifact_dir: Path


def _resolve_path(value: str | None, default: Path) -> Path:
    if value is None or not value.strip():
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load settings from an explicit mapping or the process environment."""

    values = os.environ if env is None else env
    database_url = values.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    if not database_url.strip():
        raise ValueError("DATABASE_URL cannot be blank")

    return Settings(
        database_url=database_url,
        raw_data_dir=_resolve_path(values.get("RAW_DATA_DIR"), REPOSITORY_ROOT / "data" / "raw"),
        artifact_dir=_resolve_path(values.get("ARTIFACT_DIR"), REPOSITORY_ROOT / "artifacts"),
    )
