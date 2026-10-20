# Power BI implementation blueprint

1. Run the end-to-end pipeline to create `artifacts/powerbi-inputs/*.csv`.
2. Import the seven CSVs listed in `dashboard_contract.json` into Power BI Desktop.
3. Apply the grains and relationships in `model.md`, then create the measures in `measures.md`.
4. Apply `theme.json` and build the five named pages from the checked-in PNG/PDF references.
5. Compare all headline cards with `artifacts/verified_metrics.json` before saving or exporting.

This machine does not have Power BI Desktop, so the repository deliberately does not present an
empty or fabricated PBIP/PBIX as a working deliverable. It keeps an explicit implementation
contract, DAX documentation, reviewable page evidence, and the generated PDF. A genuine PBIP/PBIX
must be authored and refreshed in Power BI Desktop.
