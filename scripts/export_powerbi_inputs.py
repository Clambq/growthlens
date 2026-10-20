"""Export privacy-safe semantic-model inputs from built analytical marts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine

from growthlens.config import load_settings
from growthlens.powerbi import export_powerbi_inputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/powerbi-inputs"))
    parser.add_argument("--schema", default="marts")
    args = parser.parse_args()
    settings = load_settings()
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        exported = export_powerbi_inputs(connection, args.output_dir, schema=args.schema)
    manifest = [item.__dict__ for item in exported]
    manifest_path = settings.artifact_dir / "powerbi_export_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
