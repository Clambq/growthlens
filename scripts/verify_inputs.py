"""Verify source files against their dataset contract before ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from growthlens.config import load_settings
from growthlens.data_contracts import HILLSTROM_CONTRACT, OLIST_CONTRACT, verify_dataset

CONTRACTS = {"olist": OLIST_CONTRACT, "hillstrom": HILLSTROM_CONTRACT}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=sorted(CONTRACTS))
    parser.add_argument("--root", type=Path, help="Directory containing the dataset CSV files")
    args = parser.parse_args()

    settings = load_settings()
    root = args.root or settings.raw_data_dir / args.dataset
    report = verify_dataset(root, CONTRACTS[args.dataset])
    payload = {
        "dataset": report.dataset,
        "root": str(report.root),
        "ok": report.ok,
        "files": [
            {
                "name": file.name,
                "path": str(file.path),
                "ok": file.ok,
                "size_bytes": file.size_bytes,
                "sha256": file.sha256,
                "columns": list(file.columns),
                "errors": list(file.errors),
            }
            for file in report.files
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
