from __future__ import annotations

from pathlib import Path

from growthlens.repository_hygiene import scan_repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_scanner_detects_sensitive_paths_and_raw_archives(tmp_path: Path) -> None:
    secret = tmp_path / "notes.md"
    secret.write_text(
        "local=C:" + "/Users/private/data and token=" + "g" + "hp_" + "a" * 36,
        encoding="utf-8",
    )
    raw = tmp_path / "dataset.csv"
    raw.write_text("customer_id\nprivate\n", encoding="utf-8")

    violations = scan_repository(tmp_path, (secret, raw))

    assert {(item.path, item.reason) for item in violations} == {
        ("notes.md", "absolute Windows user path"),
        ("notes.md", "GitHub token"),
        ("dataset.csv", "forbidden data/archive suffix .csv"),
    }


def test_tracked_repository_is_safe_for_publication() -> None:
    violations = scan_repository(PROJECT_ROOT)

    assert violations == (), "\n".join(f"{item.path}: {item.reason}" for item in violations)
