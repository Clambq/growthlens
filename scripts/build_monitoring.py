"""Build reproducible KPI anomaly and attribution artifacts from a warehouse table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from growthlens.config import load_settings
from growthlens.monitoring import detect_robust_anomalies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=28)
    parser.add_argument("--threshold", type=float, default=3.5)
    parser.add_argument("--min-periods", type=int, default=14)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    settings = load_settings()
    frame = pd.read_sql_table(
        "mart_daily_kpis",
        create_engine(settings.database_url),
        schema="marts",
    )
    output = args.output or settings.artifact_dir / "monitoring" / "alerts.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    alert_rows: list[dict[str, object]] = []
    metric_columns = [
        "merchandise_value",
        "orders",
        "average_order_value",
        "on_time_delivery_rate",
        "average_review_score",
    ]
    indexed = frame.set_index(pd.to_datetime(frame["metric_date"]))
    for metric in metric_columns:
        scored = detect_robust_anomalies(
            indexed[metric],
            window=args.window,
            threshold=args.threshold,
            min_periods=args.min_periods,
        )
        for period, row in scored.loc[scored["is_anomaly"]].iterrows():
            alert_rows.append(
                {
                    "metric": metric,
                    "period": period.date().isoformat(),
                    "actual": float(row["actual"]),
                    "baseline": float(row["baseline"]),
                    "score": float(row["score"]),
                    "direction": row["direction"],
                }
            )
    output.write_text(json.dumps(alert_rows, indent=2), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
