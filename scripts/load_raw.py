"""Load one verified public dataset into GrowthLens raw tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from growthlens.config import load_settings
from growthlens.data_contracts import HILLSTROM_CONTRACT, OLIST_CONTRACT
from growthlens.ingestion import engine_from_url, load_dataset

CONTRACTS = {"olist": OLIST_CONTRACT, "hillstrom": HILLSTROM_CONTRACT}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=sorted(CONTRACTS))
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()

    settings = load_settings()
    root = args.root or settings.raw_data_dir / args.dataset
    manifest = load_dataset(
        engine_from_url(settings.database_url),
        root,
        CONTRACTS[args.dataset],
    )
    print(
        json.dumps(
            {
                "run_id": str(manifest.run_id),
                "dataset": manifest.dataset,
                "status": manifest.status,
                "files": [
                    {
                        "source_file": file.source_file,
                        "target_table": file.target_table,
                        "source_sha256": file.source_sha256,
                        "rows_read": file.rows_read,
                        "rows_inserted": file.rows_inserted,
                    }
                    for file in manifest.files
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
