"""Minimal full-history secret scanner for release gating."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

CONTENT_PATTERNS = (
    ("AWS access key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(rb"(?:gh[psoru]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("private key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("local Windows user path", re.compile(rb"[A-Za-z]:\\Users\\[^\\\r\n]+")),
    ("local Windows user path", re.compile(rb"[A-Za-z]:/Users/[^/\r\n]+")),
    ("absolute Unix home path", re.compile(rb"/home/[A-Za-z0-9._-]+/")),
    ("Chinese mobile number", re.compile(rb"(?<!\d)1[3-9]\d{9}(?!\d)")),
    (
        "private email address",
        re.compile(
            rb"(?i)\b[A-Z0-9._%+-]+@(?!(?:example\.(?:com|org)|localhost)\b)"
            rb"[A-Z0-9.-]+\.[A-Z]{2,}\b"
        ),
    ),
)

FORBIDDEN_PATH_PATTERNS = (
    re.compile(r"(?:^|/)data/raw/", re.IGNORECASE),
    re.compile(r"\.(?:csv|parquet|zip|7z|duckdb|db|sqlite|pem|key)$", re.IGNORECASE),
    re.compile(
        r"(?:^|/)(?:\.env|kaggle\.json|credentials(?:\.json)?|\.npmrc|\.pypirc)$",
        re.IGNORECASE,
    ),
)
MAX_BLOB_BYTES = 10 * 1024 * 1024
TEXT_SUFFIXES = frozenset(
    {"", ".py", ".sql", ".md", ".yml", ".yaml", ".json", ".toml", ".txt", ".env"}
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
        for pattern in FORBIDDEN_PATH_PATTERNS:
            if pattern.search(path):
                findings.append(HistoryFinding(object_sha, path, "forbidden historical path"))
                break
        if size > MAX_BLOB_BYTES:
            findings.append(HistoryFinding(object_sha, path, "oversized historical blob"))
            continue
        if Path(path).suffix.lower() not in TEXT_SUFFIXES:
            continue
        content = subprocess.run(
            ["git", "cat-file", "blob", object_sha],
            cwd=repository,
            capture_output=True,
            check=True,
        ).stdout
        for reason, pattern in CONTENT_PATTERNS:
            if pattern.search(content):
                findings.append(HistoryFinding(object_sha, path, reason))
    return tuple(findings)
