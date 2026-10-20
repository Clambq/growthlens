"""Render a reviewable five-page dashboard PDF from Power BI extracts."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

PAGE = landscape((540, 960))
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#64748B")
TEAL = colors.HexColor("#0B6E69")
MINT = colors.HexColor("#39A69B")
GOLD = colors.HexColor("#F2A900")
CORAL = colors.HexColor("#D95D39")
BG = colors.HexColor("#F5F7FA")
GRID = colors.HexColor("#DDE3EA")
WHITE = colors.white


def _money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f}K"
    return f"R$ {value:,.0f}"


def _card(canvas: Canvas, x: float, y: float, width: float, title: str, value: str) -> None:
    canvas.setFillColor(WHITE)
    canvas.roundRect(x, y, width, 72, 8, fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(x + 14, y + 50, title.upper())
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 21)
    canvas.drawString(x + 14, y + 19, value)


def _header(canvas: Canvas, title: str, subtitle: str, page_number: int) -> None:
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE[0], PAGE[1], fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE[1] - 62, PAGE[0], 62, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 20)
    canvas.drawString(34, PAGE[1] - 32, title)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(PAGE[0] - 34, PAGE[1] - 31, "GROWTHLENS")
    canvas.setFillColor(MUTED)
    canvas.drawString(34, PAGE[1] - 82, subtitle)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE[0] - 34, 17, f"Decision dashboard  |  {page_number} / 5")


def _line_chart(
    canvas: Canvas,
    frame: pd.DataFrame,
    column: str,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
) -> None:
    canvas.setFillColor(WHITE)
    canvas.roundRect(x, y, width, height, 8, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(x + 14, y + height - 22, title)
    values = pd.to_numeric(frame[column], errors="coerce").fillna(0).to_numpy(dtype=float)
    if len(values) == 0:
        return
    plot_x, plot_y = x + 42, y + 30
    plot_w, plot_h = width - 60, height - 65
    minimum, maximum = float(values.min()), float(values.max())
    spread = maximum - minimum or 1.0
    canvas.setStrokeColor(GRID)
    for index in range(4):
        level = plot_y + index * plot_h / 3
        canvas.line(plot_x, level, plot_x + plot_w, level)
    points: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        px = plot_x + (index / max(len(values) - 1, 1)) * plot_w
        py = plot_y + ((value - minimum) / spread) * plot_h
        points.append((px, py))
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(2)
    for left, right in itertools.pairwise(points):
        canvas.line(left[0], left[1], right[0], right[1])
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(plot_x, y + 14, str(frame.iloc[0, 0])[:10])
    canvas.drawRightString(plot_x + plot_w, y + 14, str(frame.iloc[-1, 0])[:10])


def _bar_chart(
    canvas: Canvas,
    labels: list[str],
    values: list[float],
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    percent: bool = False,
) -> None:
    canvas.setFillColor(WHITE)
    canvas.roundRect(x, y, width, height, 8, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(x + 14, y + height - 22, title)
    maximum = max(values, default=1.0) or 1.0
    bar_area = height - 55
    gap = width / max(len(values), 1)
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        bar_height = (value / maximum) * (bar_area - 22)
        bx = x + gap * index + gap * 0.24
        canvas.setFillColor([TEAL, MINT, GOLD, CORAL][index % 4])
        canvas.roundRect(bx, y + 30, gap * 0.52, bar_height, 3, fill=1, stroke=0)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica-Bold", 8)
        value_label = f"{value:.1%}" if percent else f"{value:,.1f}"
        canvas.drawCentredString(bx + gap * 0.26, y + 33 + bar_height, value_label)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7)
        short = label if stringWidth(label, "Helvetica", 7) < gap * 0.8 else label[:13] + "..."
        canvas.drawCentredString(bx + gap * 0.26, y + 15, short)


def _table(
    canvas: Canvas,
    rows: list[list[str]],
    headers: list[str],
    x: float,
    y: float,
    widths: list[float],
    title: str,
) -> None:
    row_height = 22
    height = 38 + row_height * (len(rows) + 1)
    canvas.setFillColor(WHITE)
    canvas.roundRect(x, y, sum(widths), height, 8, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(x + 12, y + height - 21, title)
    top = y + height - 38
    cursor = x
    canvas.setFillColor(colors.HexColor("#E7F3F1"))
    canvas.rect(x, top - row_height, sum(widths), row_height, fill=1, stroke=0)
    for header, width in zip(headers, widths, strict=True):
        canvas.setFillColor(TEAL)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(cursor + 6, top - 15, header)
        cursor += width
    for row_index, row in enumerate(rows):
        row_top = top - row_height * (row_index + 1)
        cursor = x
        for value, width in zip(row, widths, strict=True):
            canvas.setFillColor(INK)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(cursor + 6, row_top - 15, value[:30])
            cursor += width


def _load(input_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(input_dir / f"{name}.csv")


def render_dashboard(input_dir: Path, metrics_path: Path, output_path: Path) -> None:
    daily = _load(input_dir, "daily_kpis")
    cohorts = _load(input_dir, "customer_cohorts")
    delivery = _load(input_dir, "delivery_summary")
    sellers = _load(input_dir, "seller_scorecard")
    experiment = _load(input_dir, "experiment_summary")
    quality = _load(input_dir, "experiment_quality")
    metrics: dict[str, Any] = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output_path), pagesize=PAGE, pageCompression=1)
    canvas.setTitle("GrowthLens Decision Dashboard")

    _header(canvas, "Management Overview", "Olist commerce performance - descriptive evidence", 1)
    total_merchandise = float(daily["merchandise_value"].sum())
    total_orders = int(daily["orders"].sum())
    total_customers = int(daily["customers"].sum())
    _card(canvas, 34, 374, 206, "Merchandise value", _money(total_merchandise))
    _card(canvas, 252, 374, 206, "Orders", f"{total_orders:,}")
    _card(canvas, 470, 374, 206, "Customers (daily sum)", f"{total_customers:,}")
    _card(canvas, 688, 374, 238, "Average order value", _money(total_merchandise / total_orders))
    _line_chart(canvas, daily, "merchandise_value", 34, 72, 574, 282, "Daily merchandise value")
    _line_chart(canvas, daily, "orders", 626, 72, 300, 282, "Daily orders")
    canvas.showPage()

    _header(canvas, "Revenue and Customer Growth", "Cohort evidence and commercial demand", 2)
    _line_chart(canvas, daily, "customers", 34, 272, 560, 180, "Daily customers")
    _line_chart(canvas, daily, "average_order_value", 612, 272, 314, 180, "Average order value")
    cohort_summary = (
        cohorts.groupby("month_offset", as_index=False)["active_customers"].sum().head(8)
    )
    _bar_chart(
        canvas,
        [f"M{int(value)}" for value in cohort_summary["month_offset"]],
        cohort_summary["active_customers"].astype(float).tolist(),
        34,
        70,
        892,
        180,
        "Active customers by months since acquisition",
    )
    canvas.showPage()

    _header(
        canvas,
        "Fulfillment and Seller Operations",
        "Associations support prioritization; they do not prove causality",
        3,
    )
    by_status = delivery.groupby("is_late_delivery", as_index=False).agg(
        delivered_orders=("delivered_orders", "sum"),
        review=("average_review_score", "mean"),
    )
    labels = ["Late" if bool(value) else "On time" for value in by_status["is_late_delivery"]]
    _bar_chart(
        canvas,
        labels,
        by_status["review"].astype(float).tolist(),
        34,
        252,
        350,
        200,
        "Average review score",
    )
    eligible = sellers[sellers["is_priority_eligible"].astype(bool)].copy()
    eligible = eligible.sort_values("priority_score", ascending=False).head(8)
    seller_rows = [
        [
            str(row.seller_key),
            f"{int(row.commercial_order_count):,}",
            f"{float(row.late_delivery_rate):.1%}",
            f"{float(row.average_review_score):.2f}",
            f"{float(row.priority_score):.3f}",
        ]
        for row in eligible.itertuples()
    ]
    _table(
        canvas,
        seller_rows,
        ["Seller", "Orders", "Late rate", "Review", "Priority"],
        404,
        214,
        [116, 74, 82, 72, 90],
        "Priority-eligible sellers",
    )
    _line_chart(canvas, daily, "on_time_delivery_rate", 34, 54, 350, 176, "On-time delivery rate")
    canvas.showPage()

    _header(
        canvas,
        "Experiment Decision",
        "Hillstrom randomized experiment - confirmatory conversion outcome",
        4,
    )
    experiment = experiment.sort_values("segment")
    _bar_chart(
        canvas,
        experiment["segment"].astype(str).tolist(),
        experiment["conversion_rate"].astype(float).tolist(),
        34,
        190,
        510,
        262,
        "Conversion rate by randomized group",
        percent=True,
    )
    metric_records = metrics["observed_results"]["experiment"]
    rows = []
    for name, record in sorted(metric_records.items()):
        if record.get("analysis_type") != "randomized_experiment":
            continue
        interval = record["confidence_interval"]
        rows.append(
            [
                name.replace("_conversion_effect", "").replace("_", " ").title(),
                f"{record['value']:.2%}",
                f"[{interval['low']:.2%}, {interval['high']:.2%}]",
                f"{record['holm_adjusted_p_value']:.4f}",
            ]
        )
    _table(
        canvas,
        rows,
        ["Treatment", "Abs. lift", "95% CI", "Holm p"],
        564,
        237,
        [104, 72, 126, 74],
        "Primary outcome effects",
    )
    duplicate_count = int(quality["duplicate_customer_count"].max())
    _card(canvas, 564, 142, 174, "Duplicate assignments", f"{duplicate_count:,}")
    srm = metric_records["sample_ratio_p_value"]["value"]
    _card(canvas, 752, 142, 174, "SRM p-value", f"{float(srm):.4f}")
    canvas.setFillColor(colors.HexColor("#FFF4D6"))
    canvas.roundRect(34, 74, 892, 50, 8, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(50, 101, "Decision rule")
    canvas.setFont("Helvetica", 9)
    canvas.drawString(
        50,
        84,
        "Interpret effects only after SRM, duplicate, interval, and Holm checks pass.",
    )
    canvas.showPage()

    _header(canvas, "Data Quality", "Lineage, reproducibility, and interpretation guardrails", 5)
    provenance = metrics["source_provenance"]
    provenance_rows = [
        [source, str(record["run_id"])[:18], str(len(record.get("sha256", []))), "Verified"]
        for source, record in sorted(provenance.items())
    ]
    _table(
        canvas,
        provenance_rows,
        ["Dataset", "Run ID", "Files", "Status"],
        34,
        260,
        [150, 246, 82, 116],
        "Latest audited source runs",
    )
    quality_rows = [
        [
            str(row.segment),
            f"{int(row.observed_count):,}",
            f"{float(row.observed_share):.2%}",
            str(int(row.duplicate_customer_count)),
        ]
        for row in quality.itertuples()
    ]
    _table(
        canvas,
        quality_rows,
        ["Segment", "N", "Share", "Duplicates"],
        646,
        260,
        [112, 70, 84, 92],
        "Experiment assignment quality",
    )
    notes = [
        "Commerce metrics are descriptive; delivery/review findings are associational.",
        "The two public datasets are independent cases and are never entity-joined.",
        "Raw customer, order, and seller identifiers are excluded from BI exports.",
        "Every headline statistic is generated from audited source runs.",
    ]
    canvas.setFillColor(WHITE)
    canvas.roundRect(34, 66, 892, 156, 8, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(50, 195, "Interpretation guardrails")
    canvas.setFont("Helvetica", 10)
    for index, note in enumerate(notes):
        canvas.setFillColor(TEAL)
        canvas.circle(54, 166 - index * 27, 3, fill=1, stroke=0)
        canvas.setFillColor(INK)
        canvas.drawString(68, 162 - index * 27, note)
    canvas.showPage()
    canvas.save()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("artifacts/powerbi-inputs"))
    parser.add_argument("--metrics", type=Path, default=Path("artifacts/verified_metrics.json"))
    parser.add_argument("--output", type=Path, default=Path("powerbi/GrowthLens-dashboard.pdf"))
    args = parser.parse_args()
    render_dashboard(args.input_dir, args.metrics, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
