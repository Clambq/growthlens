# Power BI handoff

1. Run the end-to-end pipeline to create `artifacts/powerbi-inputs/*.csv`.
2. Open `GrowthLens.pbip` in Power BI Desktop (November 2024 or newer).
3. Point the six Power Query sources to the generated input directory if prompted.
4. Apply `theme.json`, verify the five named pages, and refresh.
5. Compare all headline cards with `artifacts/verified_metrics.json` before saving or exporting.

The repository keeps source-control-friendly PBIP/TMDL, DAX documentation,
reviewable page evidence, and the exported PDF. A `.pbix` binary must be created
by Power BI Desktop; this repository never renames or fabricates another file as
a PBIX.
