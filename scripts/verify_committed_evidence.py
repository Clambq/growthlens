"""Verify that committed evidence is internally consistent and reviewable."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts"
    metrics_path = artifacts / "verified_metrics.json"
    manifest = json.loads((artifacts / "run_manifest.json").read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    if manifest["verified_metrics_sha256"] != expected_hash:
        raise RuntimeError("run manifest does not match committed verified metrics")
    subprocess.run(
        ["git", "cat-file", "-e", f"{manifest['git_sha']}^{{commit}}"],
        cwd=root,
        check=True,
        capture_output=True,
    )

    contract = json.loads(
        (root / "powerbi" / "dashboard_contract.json").read_text(encoding="utf-8")
    )
    if contract["editable_power_bi_project_included"] is not False:
        raise RuntimeError("dashboard artifact boundary is not explicit")
    pdf = root / "powerbi" / "GrowthLens-dashboard.pdf"
    if not pdf.read_bytes().startswith(b"%PDF"):
        raise RuntimeError("dashboard PDF is missing or invalid")
    screenshots = sorted((root / "powerbi" / "screenshots").glob("GrowthLens-*.png"))
    if len(screenshots) != len(contract["pages"]):
        raise RuntimeError("dashboard screenshot count does not match page contract")
    if any(not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in screenshots):
        raise RuntimeError("dashboard screenshot is not a valid PNG")
    print("committed evidence verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
