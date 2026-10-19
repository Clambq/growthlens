# GrowthLens

GrowthLens is a reproducible analytics portfolio built around two independent public-data
cases:

1. **Commerce Performance Observatory** — SQL/dbt modeling, metric governance, anomaly
   monitoring, and diagnostic analysis using the anonymized Olist marketplace dataset.
2. **Experiment Decision Lab** — validity checks, treatment-effect estimation, multiplicity
   control, and variance reduction using the randomized Hillstrom email experiment.

The cases share engineering standards but are never joined or represented as one company.
The repository is being implemented from the checked-in
[design](docs/superpowers/specs/2026-10-19-growthlens-design.md) and
[implementation plan](docs/superpowers/plans/2026-10-19-growthlens-implementation.md).

## Local baseline

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,analytics]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
docker compose up -d --wait postgres
```

Raw public datasets, credentials, local database volumes, and unverified generated outputs are
intentionally excluded from version control.
