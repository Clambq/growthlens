"""Fail-fast orchestration for the reproducible GrowthLens pipeline."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy.engine import make_url

from growthlens.config import REPOSITORY_ROOT, Settings
from growthlens.data_contracts import HILLSTROM_CONTRACT, OLIST_CONTRACT, verify_dataset
from growthlens.ingestion import engine_from_url, load_dataset


class PipelineStageError(RuntimeError):
    """A stage failed a quality gate and downstream work must stop."""


@dataclass(frozen=True, slots=True)
class StageResult:
    name: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class PipelineResult:
    succeeded: bool
    stages: tuple[StageResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "succeeded": self.succeeded,
            "stages": [asdict(stage) for stage in self.stages],
        }


StageHandler = Callable[[Settings], str]


def _verify(settings: Settings) -> str:
    reports = [
        verify_dataset(settings.raw_data_dir / "olist", OLIST_CONTRACT),
        verify_dataset(settings.raw_data_dir / "hillstrom", HILLSTROM_CONTRACT),
    ]
    failures = [
        f"{report.dataset}: {error}"
        for report in reports
        for file in report.files
        for error in file.errors
    ]
    if failures:
        raise PipelineStageError("dataset contract failed: " + "; ".join(failures))
    return f"verified {sum(len(report.files) for report in reports)} source files"


def _load(settings: Settings) -> str:
    engine = engine_from_url(settings.database_url)
    try:
        manifests = [
            load_dataset(engine, settings.raw_data_dir / "olist", OLIST_CONTRACT),
            load_dataset(engine, settings.raw_data_dir / "hillstrom", HILLSTROM_CONTRACT),
        ]
    finally:
        engine.dispose()
    inserted = sum(file.rows_inserted for manifest in manifests for file in manifest.files)
    return f"completed {len(manifests)} audited loads; inserted {inserted} new rows"


def _subprocess_environment(settings: Settings) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "DATABASE_URL": settings.database_url,
            "RAW_DATA_DIR": str(settings.raw_data_dir),
            "ARTIFACT_DIR": str(settings.artifact_dir),
        }
    )
    url = make_url(settings.database_url)
    if url.drivername.startswith("duckdb"):
        database = Path(url.database or "artifacts/growthlens.duckdb")
        if not database.is_absolute():
            database = REPOSITORY_ROOT / database
        environment["DBT_TARGET"] = "duckdb"
        environment["GROWTHLENS_DUCKDB_PATH"] = str(database)
    else:
        environment.setdefault("DBT_TARGET", "postgres")
    return environment


def _run(command: Sequence[str], settings: Settings) -> str:
    result = subprocess.run(
        list(command),
        cwd=REPOSITORY_ROOT,
        env=_subprocess_environment(settings),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        diagnostic = (result.stdout + "\n" + result.stderr).strip()[-3000:]
        raise PipelineStageError(f"command failed ({' '.join(command)}):\n{diagnostic}")
    return result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "completed"


def _dbt(settings: Settings) -> str:
    return _run(
        (
            sys.executable,
            "-m",
            "dbt.cli.main",
            "build",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
        ),
        settings,
    )


def _artifacts(settings: Settings) -> str:
    return _run((sys.executable, "scripts/build_artifacts.py"), settings)


def _powerbi(settings: Settings) -> str:
    _run(
        (
            sys.executable,
            "scripts/export_powerbi_inputs.py",
            "--output-dir",
            str(settings.artifact_dir / "powerbi-inputs"),
        ),
        settings,
    )
    return _run(
        (
            sys.executable,
            "scripts/render_powerbi_dashboard.py",
            "--input-dir",
            str(settings.artifact_dir / "powerbi-inputs"),
            "--metrics",
            str(settings.artifact_dir / "verified_metrics.json"),
            "--output",
            "powerbi/GrowthLens-dashboard.pdf",
        ),
        settings,
    )


STAGE_HANDLERS: dict[str, StageHandler] = {
    "verify": _verify,
    "load": _load,
    "dbt": _dbt,
    "artifacts": _artifacts,
    "powerbi": _powerbi,
}


def run_pipeline(stages: Sequence[str], settings: Settings) -> PipelineResult:
    """Run named stages in order and stop immediately after the first failure."""

    unknown = [stage for stage in stages if stage not in STAGE_HANDLERS]
    if unknown:
        available = ", ".join(STAGE_HANDLERS)
        raise ValueError(f"unknown pipeline stage {unknown[0]!r}; available stages: {available}")
    results: list[StageResult] = []
    for name in stages:
        try:
            detail = STAGE_HANDLERS[name](settings)
        except Exception as error:
            results.append(StageResult(name=name, status="failed", detail=str(error)))
            return PipelineResult(succeeded=False, stages=tuple(results))
        results.append(StageResult(name=name, status="succeeded", detail=detail))
    return PipelineResult(succeeded=True, stages=tuple(results))
