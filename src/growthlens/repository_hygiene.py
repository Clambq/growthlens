"""Public-repository privacy and artifact policy checks."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_SUFFIXES = frozenset({".csv", ".parquet", ".zip", ".7z", ".duckdb", ".db", ".sqlite"})
FORBIDDEN_NAMES = frozenset({".env", "kaggle.json", "credentials", "credentials.json"})
MAX_FILE_BYTES = 5 * 1024 * 1024
TEXT_SUFFIXES = frozenset(
    {
        ".py",
        ".sql",
        ".md",
        ".yml",
        ".yaml",
        ".json",
        ".toml",
        ".txt",
        ".env",
        ".tmdl",
        ".pbip",
        ".pbir",
        ".pbism",
    }
)
CONTENT_RULES = (
    ("absolute Windows user path", re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.I)),
    ("absolute Unix home path", re.compile(r"/home/[A-Za-z0-9._-]+/")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[ps]_[A-Za-z0-9]{30,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Chinese mobile number", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    (
        "private email address",
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@(?!example\.com\b)[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    ),
)


@dataclass(frozen=True, slots=True)
class HygieneViolation:
    path: str
    reason: str


def tracked_paths(root: Path) -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    return tuple(root / path for path in result.stdout.decode("utf-8").split("\0") if path)


def scan_repository(
    root: Path, paths: Iterable[Path] | None = None
) -> tuple[HygieneViolation, ...]:
    """Scan tracked or supplied paths for publish-blocking data and secrets."""

    repository = Path(root).resolve()
    candidates = tuple(paths) if paths is not None else tracked_paths(repository)
    violations: list[HygieneViolation] = []
    for candidate in candidates:
        path = candidate if candidate.is_absolute() else repository / candidate
        if not path.is_file():
            continue
        relative = path.resolve().relative_to(repository).as_posix()
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES:
            violations.append(HygieneViolation(relative, f"forbidden data/archive suffix {suffix}"))
        if path.name.lower() in FORBIDDEN_NAMES or suffix == ".env":
            violations.append(HygieneViolation(relative, "forbidden credential filename"))
        size = path.stat().st_size
        approved_large = relative.startswith("powerbi/screenshots/") or relative == (
            "powerbi/GrowthLens-dashboard.pdf"
        )
        if size > MAX_FILE_BYTES and not approved_large:
            violations.append(HygieneViolation(relative, f"oversized tracked file: {size} bytes"))
        if suffix not in TEXT_SUFFIXES or size > 2 * 1024 * 1024:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for reason, pattern in CONTENT_RULES:
            if pattern.search(text):
                violations.append(HygieneViolation(relative, reason))
    return tuple(violations)
