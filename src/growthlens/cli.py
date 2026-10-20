"""GrowthLens command-line interface."""

from __future__ import annotations

import argparse
import json

from growthlens.config import load_settings
from growthlens.pipeline import run_pipeline

COMMAND_STAGES = {
    "verify": ("verify",),
    "build": ("load", "dbt"),
    "report": ("artifacts", "powerbi"),
    "all": ("verify", "load", "dbt", "artifacts", "powerbi"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="growthlens")
    parser.add_argument("command", choices=COMMAND_STAGES)
    arguments = parser.parse_args(argv)
    result = run_pipeline(COMMAND_STAGES[arguments.command], load_settings())
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
