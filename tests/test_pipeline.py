from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from growthlens.config import Settings
from growthlens.pipeline import PipelineStageError, run_pipeline


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'pipeline.sqlite'}",
        raw_data_dir=tmp_path / "raw",
        artifact_dir=tmp_path / "artifacts",
    )


def test_pipeline_runs_requested_stages_in_order(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    observed: list[str] = []

    def handler(name: str):
        def execute(_settings: Settings) -> str:
            observed.append(name)
            return f"{name} complete"

        return execute

    monkeypatch.setattr(
        "growthlens.pipeline.STAGE_HANDLERS",
        {name: handler(name) for name in ("verify", "load", "dbt", "artifacts", "powerbi")},
    )

    result = run_pipeline(("verify", "load", "dbt", "artifacts", "powerbi"), settings)

    assert result.succeeded is True
    assert observed == ["verify", "load", "dbt", "artifacts", "powerbi"]
    assert [stage.status for stage in result.stages] == ["succeeded"] * 5


def test_pipeline_stops_after_quality_failure(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    observed: list[str] = []

    def verify(_settings: Settings) -> str:
        observed.append("verify")
        raise PipelineStageError("dataset contract failed: missing orders.csv")

    def should_not_run(_settings: Settings) -> str:
        observed.append("load")
        return "unexpected"

    monkeypatch.setattr(
        "growthlens.pipeline.STAGE_HANDLERS", {"verify": verify, "load": should_not_run}
    )

    result = run_pipeline(("verify", "load"), settings)

    assert result.succeeded is False
    assert observed == ["verify"]
    assert result.stages[-1].status == "failed"
    assert "missing orders.csv" in result.stages[-1].detail


def test_pipeline_rerun_is_allowed_and_unknown_stage_is_actionable(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    calls = 0

    def idempotent(_settings: Settings) -> str:
        nonlocal calls
        calls += 1
        return "verified"

    monkeypatch.setattr("growthlens.pipeline.STAGE_HANDLERS", {"verify": idempotent})

    assert run_pipeline(("verify",), settings).succeeded
    assert run_pipeline(("verify",), settings).succeeded
    assert calls == 2
    with pytest.raises(ValueError, match=r"unknown pipeline stage.*verify"):
        run_pipeline(("mystery",), settings)


def test_load_stage_disposes_database_engine(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    class FakeEngine:
        disposed = False

        def dispose(self) -> None:
            self.disposed = True

    engine = FakeEngine()
    manifest = SimpleNamespace(files=(SimpleNamespace(rows_inserted=0),))
    monkeypatch.setattr("growthlens.pipeline.engine_from_url", lambda _url: engine)
    monkeypatch.setattr("growthlens.pipeline.load_dataset", lambda *_args: manifest)

    result = run_pipeline(("load",), settings)

    assert result.succeeded is True
    assert engine.disposed is True
