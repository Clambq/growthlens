"""Minimal full-history secret scanner for release gating."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SECRET_PATTERNS = (
    ("AWS access key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(rb"gh[ps]_[A-Za-z0-9]{30,}")),
    ("private key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


@dataclass(frozen=True, slots=True)
class HistoryFinding:
    object_sha: str
    path: str
    reason: str


def scan_git_history(root: Path) -> tuple[HistoryFinding, ...]:
    repository = Path(root)
    listed = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    findings: list[HistoryFinding] = []
    seen: set[str] = set()
    for entry in listed:
        object_sha, _, path = entry.partition(" ")
        if not path or object_sha in seen:
            continue
        seen.add(object_sha)
        object_type = subprocess.run(
            ["git", "cat-file", "-t", object_sha],
            cwd=repository,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if object_type != "blob":
            continue
        size = int(
            subprocess.run(
                ["git", "cat-file", "-s", object_sha],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        if size > 2 * 1024 * 1024:
            continue
        content = subprocess.run(
            ["git", "cat-file", "blob", object_sha],
            cwd=repository,
            capture_output=True,
            check=True,
        ).stdout
        for reason, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append(HistoryFinding(object_sha, path, reason))
    return tuple(findings)
