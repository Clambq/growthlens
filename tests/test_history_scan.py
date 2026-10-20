from __future__ import annotations

import subprocess
from pathlib import Path

from growthlens.history_scan import scan_git_history


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)


def test_history_scanner_finds_secret_removed_from_worktree(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "GrowthLens Test")
    _git(tmp_path, "config", "user.email", "test@example.com")
    secret = tmp_path / "old.txt"
    secret.write_text("key=" + "AKIA" + "A" * 16, encoding="utf-8")
    _git(tmp_path, "add", "old.txt")
    _git(tmp_path, "commit", "-m", "add old file")
    secret.unlink()
    _git(tmp_path, "add", "-u")
    _git(tmp_path, "commit", "-m", "remove old file")

    findings = scan_git_history(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == "old.txt"
    assert findings[0].reason == "AWS access key"


def test_history_scanner_finds_raw_dataset_removed_from_worktree(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "GrowthLens Test")
    _git(tmp_path, "config", "user.email", "test@example.com")
    raw = tmp_path / "data" / "raw" / "customers.csv"
    raw.parent.mkdir(parents=True)
    raw.write_text("customer_id\nprivate-1\n", encoding="utf-8")
    _git(tmp_path, "add", "data/raw/customers.csv")
    _git(tmp_path, "commit", "-m", "add raw file")
    raw.unlink()
    _git(tmp_path, "add", "-u")
    _git(tmp_path, "commit", "-m", "remove raw file")

    findings = scan_git_history(tmp_path)

    assert any(finding.reason == "forbidden historical path" for finding in findings)
