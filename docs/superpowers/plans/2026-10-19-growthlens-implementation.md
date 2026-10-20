# GrowthLens Implementation Plan

> **Scope amendment (2026-10-19):** Power BI Desktop is unavailable in the execution
> environment. The accepted BI deliverable is therefore the tested seven-table export contract,
> model/DAX/theme implementation blueprint, and five-page PDF/PNG rendered preview. Empty,
> hand-authored PBIP/PBIX scaffolds are explicitly rejected. Any later Desktop-authored PBIP/PBIX
> must follow `powerbi/README.md` and reconcile to the committed metric artifact.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a reproducible portfolio-grade analytics platform that demonstrates SQL modeling, data quality, business monitoring, experiment analysis, Power BI reporting, and evidence-backed resume claims.

**Architecture:** A standalone `growthlens` repository uses Dockerized PostgreSQL for raw and analytical data, dbt for transformations and data tests, a focused Python package for monitoring and statistical inference, and Power BI for the final decision dashboard. Olist commerce data and Hillstrom experiment data remain separate cases that share engineering standards, verified metric artifacts, and reporting conventions.

**Tech Stack:** Python 3.11+, PostgreSQL 16, Docker Compose, dbt Core with `dbt-postgres`, pandas, NumPy, SciPy, statsmodels, scikit-learn, SQLAlchemy, pytest, Ruff, Power BI Desktop, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-19-growthlens-design.md`

## Global Constraints

- Create all implementation files under the standalone folder `growthlens/`; initialize it as an independent Git repository.
- Work on branch `codex/initial-implementation`; do not implement directly on the repository's `main` branch.
- Preserve the two datasets as independent public cases; never join their entities or imply they belong to one company.
- Do not commit raw Olist or Hillstrom data, Kaggle credentials, `.env`, database volumes, or private information.
- Treat Olist order timestamps as an operational lifecycle, not a clickstream funnel.
- Distinguish merchandise value, freight, and payment value; do not call all three GMV.
- Describe delivery and review results as associations unless an identified causal design supports stronger language.
- Freeze the Hillstrom primary outcome, comparison family, and adjustment rules before reading or reporting effects.
- Do not create resume bullets with effect numbers until the reproducible pipeline has generated `artifacts/verified_metrics.json`.
- Use tests first for every behavior-bearing Python or SQL change. Configuration-only files are paired with the first behavior that consumes them.
- Use UTF-8 and platform-independent paths; all documented commands must work from PowerShell on Windows.
- Publish a public GitHub repository only after repository hygiene, licensing, data-provenance, and secret scans pass.

## Review Focus

1. **Multi-table fan-out:** joining order items, payments, and reviews must not duplicate orders or monetary values. Task 5 adds fixture reconciliation tests that fail on fan-out.
2. **Input drift and partial downloads:** missing files, renamed columns, unexpected encodings, or changed source files must fail before loading. Task 2 adds contract and UTF-8/path tests.
3. **Idempotent ingestion:** loading the same files twice must preserve row counts while recording a new audit result. Task 3 adds PostgreSQL integration tests.
4. **Invalid experiment inference:** SRM, duplicate customers, post-treatment CUPED covariates, or uncorrected multiple comparisons must be rejected or explicitly reported. Tasks 8 and 9 add statistical contract tests.
5. **Public-repository leakage:** raw data, credentials, local paths, generated database files, and personal identifiers must never enter Git history. Task 13 adds repository hygiene and secret-scan gates before publication.

---

### Task 1: Standalone repository and executable Python baseline

**Files:**
- Create: `growthlens/.gitignore`
- Create: `growthlens/.env.example`
- Create: `growthlens/pyproject.toml`
- Create: `growthlens/docker-compose.yml`
- Create: `growthlens/Makefile`
- Create: `growthlens/README.md`
- Create: `growthlens/src/growthlens/__init__.py`
- Create: `growthlens/src/growthlens/config.py`
- Create: `growthlens/tests/test_config.py`
- Copy: `docs/superpowers/specs/2026-10-19-growthlens-design.md` to `growthlens/docs/superpowers/specs/2026-10-19-growthlens-design.md`
- Copy: this plan to `growthlens/docs/superpowers/plans/2026-10-19-growthlens-implementation.md`

**Interfaces:**
- Produces: `Settings(database_url: str, raw_data_dir: Path, artifact_dir: Path)` and `load_settings(env: Mapping[str, str] | None = None) -> Settings`.
- Consumes: no project code.

- [ ] **Step 1: Initialize the independent repository and branch**

Create `growthlens/`, run `git init -b main`, make an empty initial commit containing only copied spec/plan metadata if required by Git, and create `codex/initial-implementation` before product implementation.

- [ ] **Step 2: Write the failing settings tests**

Test that `load_settings({})` returns relative workspace defaults resolved beneath the repository, Windows-style override paths are accepted, and a blank `DATABASE_URL` raises `ValueError`.

- [ ] **Step 3: Run the settings tests to verify RED**

Run: `pytest tests/test_config.py -v`

Expected: collection fails because `growthlens.config` does not exist.

- [ ] **Step 4: Implement the minimal package and project configuration**

Implement the exact `Settings` and `load_settings` interfaces, declare Python and development dependencies, define PostgreSQL 16 in Compose, and add targets for `test`, `lint`, `db-up`, and `db-down`.

- [ ] **Step 5: Verify the baseline**

Run: `pytest tests/test_config.py -v` and `ruff check src tests`.

Expected: all tests pass and Ruff reports no violations.

- [ ] **Step 6: Commit**

Commit message: `chore: bootstrap GrowthLens project`.

### Task 2: Dataset contracts and pre-load verification

**Files:**
- Create: `growthlens/data/README.md`
- Create: `growthlens/src/growthlens/data_contracts.py`
- Create: `growthlens/scripts/verify_inputs.py`
- Create: `growthlens/scripts/download_hillstrom.py`
- Create: `growthlens/tests/fixtures/contracts/`
- Create: `growthlens/tests/test_data_contracts.py`

**Interfaces:**
- Consumes: `Settings.raw_data_dir` from Task 1.
- Produces: `FileContract(name: str, required_columns: frozenset[str], encoding: str)`, `DatasetContract(name: str, files: tuple[FileContract, ...])`, `FileCheck`, `VerificationReport`, and `verify_dataset(root: Path, contract: DatasetContract) -> VerificationReport`.

- [ ] **Step 1: Write failing contract tests**

Cover a valid UTF-8 CSV, missing file, missing column, duplicate header, malformed encoding, a path containing Chinese characters, and Olist's required nine-file manifest.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_data_contracts.py -v`.

Expected: import failure for `growthlens.data_contracts`.

- [ ] **Step 3: Implement contracts and verification CLI**

Implement deterministic header-only checks, file size/hash capture, structured error messages, Hillstrom download with explicit source URL, and provenance documentation. Do not download Olist automatically without Kaggle credentials; document manual and Kaggle CLI paths.

- [ ] **Step 4: Verify GREEN and full suite**

Run: `pytest tests/test_data_contracts.py -v`, `pytest -q`, and `ruff check src scripts tests`.

Expected: all checks pass.

- [ ] **Step 5: Commit**

Commit message: `feat: validate public dataset inputs`.

### Task 3: Audited and idempotent PostgreSQL ingestion

**Files:**
- Create: `growthlens/sql/bootstrap/001_schemas.sql`
- Create: `growthlens/sql/bootstrap/002_audit_tables.sql`
- Create: `growthlens/src/growthlens/ingestion.py`
- Create: `growthlens/scripts/load_raw.py`
- Create: `growthlens/tests/integration/test_ingestion_postgres.py`
- Modify: `growthlens/Makefile`

**Interfaces:**
- Consumes: verified `DatasetContract` and `Settings.database_url`.
- Produces: `LoadManifest(run_id: UUID, dataset: str, files: tuple[LoadedFile, ...])`, `load_dataset(engine: Engine, root: Path, contract: DatasetContract) -> LoadManifest`, and raw tables with `_loaded_at`, `_source_file`, `_row_hash`, `_run_id`.

- [ ] **Step 1: Write failing PostgreSQL integration tests**

Use minimal Olist and Hillstrom fixture files to assert first-load row counts, audit metadata, transactional rollback on a bad row, and unchanged business row counts after loading identical files twice.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/integration/test_ingestion_postgres.py -v` with the test database running.

Expected: import failure for `growthlens.ingestion`.

- [ ] **Step 3: Implement bootstrap SQL, loader, and CLI**

Use SQLAlchemy transactions, explicit table mappings, staging tables, deterministic row hashes, and an ingestion audit record for each attempt.

- [ ] **Step 4: Verify GREEN and rollback behavior**

Run the targeted integration test, `pytest -q`, and a manual double-load against the Compose database.

Expected: all tests pass; the second load creates an audit event without duplicating source rows.

- [ ] **Step 5: Commit**

Commit message: `feat: add audited raw data ingestion`.

### Task 4: dbt sources, staging models, and quality gates

**Files:**
- Create: `growthlens/dbt/dbt_project.yml`
- Create: `growthlens/dbt/profiles.example.yml`
- Create: `growthlens/dbt/models/sources.yml`
- Create: `growthlens/dbt/models/staging/commerce/`
- Create: `growthlens/dbt/models/staging/experiments/`
- Create: `growthlens/dbt/tests/`
- Create: `growthlens/tests/integration/test_dbt_staging.py`
- Modify: `growthlens/pyproject.toml`
- Modify: `growthlens/Makefile`

**Interfaces:**
- Consumes: raw PostgreSQL tables from Task 3.
- Produces: typed `stg_olist_*` and `stg_hillstrom_customers` relations plus dbt source freshness and schema tests.

- [ ] **Step 1: Write failing staging contract tests**

Assert model names, expected columns, customer identifier semantics, timestamp ordering flags, accepted categorical values, and that a deliberate broken fixture causes `dbt build` to fail.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/integration/test_dbt_staging.py -v`.

Expected: failure because the dbt project and staging relations do not exist.

- [ ] **Step 3: Implement dbt project and staging models**

Add explicit casts, normalized names, non-destructive anomaly flags, relationship tests, accepted-values tests, and source documentation.

- [ ] **Step 4: Verify GREEN**

Run: `dbt build --project-dir dbt --profiles-dir dbt`, the targeted integration test, and `pytest -q`.

Expected: dbt build and all Python tests pass.

- [ ] **Step 5: Commit**

Commit message: `feat: model and test staging data`.

### Task 5: Grain-safe commerce marts and metric catalog

**Files:**
- Create: `growthlens/dbt/models/intermediate/commerce/`
- Create: `growthlens/dbt/models/marts/commerce/fct_orders.sql`
- Create: `growthlens/dbt/models/marts/commerce/fct_order_items.sql`
- Create: `growthlens/dbt/models/marts/commerce/dim_customers.sql`
- Create: `growthlens/dbt/models/marts/commerce/dim_products.sql`
- Create: `growthlens/dbt/models/marts/commerce/dim_sellers.sql`
- Create: `growthlens/dbt/models/marts/commerce/dim_dates.sql`
- Create: `growthlens/dbt/models/marts/commerce/mart_daily_kpis.sql`
- Create: `growthlens/dbt/models/marts/commerce/schema.yml`
- Create: `growthlens/reports/metric_catalog.md`
- Create: `growthlens/tests/integration/test_commerce_metrics.py`

**Interfaces:**
- Consumes: `stg_olist_*` relations from Task 4.
- Produces: documented fact/dimension relations and daily KPIs with `merchandise_value`, `freight_value`, `payment_value`, `orders`, `customers`, `average_order_value`, `repeat_customer_rate`, `on_time_delivery_rate`, and `average_review_score`.

- [ ] **Step 1: Write failing metric reconciliation tests**

Fixture cases must include one order with multiple items and payments, one canceled order, one customer with two orders, duplicate review rows, and early/late deliveries. Assert exact totals and prove no fan-out.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/integration/test_commerce_metrics.py -v`.

Expected: missing marts or wrong relation errors.

- [ ] **Step 3: Implement intermediate models, marts, and metric documentation**

Pre-aggregate each one-to-many relation at its intended grain before joining. Freeze order-status inclusion rules in one intermediate model and document every numerator, denominator, time grain, and exclusion.

- [ ] **Step 4: Verify GREEN and dbt tests**

Run targeted tests, `dbt build`, and `pytest -q`.

Expected: exact fixture metrics and the full suite pass.

- [ ] **Step 5: Commit**

Commit message: `feat: build grain-safe commerce marts`.

### Task 6: KPI monitoring and anomaly attribution

**Files:**
- Create: `growthlens/src/growthlens/monitoring.py`
- Create: `growthlens/tests/test_monitoring.py`
- Create: `growthlens/scripts/build_monitoring.py`
- Create: `growthlens/dbt/models/marts/commerce/mart_kpi_alerts.sql`

**Interfaces:**
- Consumes: daily KPI frames from `mart_daily_kpis`.
- Produces: `Alert(metric: str, period: date, actual: float, baseline: float, score: float, direction: str)`, `detect_robust_anomalies(series: pd.Series, window: int, threshold: float, min_periods: int) -> pd.DataFrame`, and `attribute_change(frame: pd.DataFrame, value_col: str, dimension_col: str, before: DateRange, after: DateRange) -> pd.DataFrame`.

- [ ] **Step 1: Write failing monitoring tests**

Cover a constant series, missing days, insufficient history, a known spike, a known drop, zero baseline, and contributions that sum to the total period change.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_monitoring.py -v`.

Expected: import failure for `growthlens.monitoring`.

- [ ] **Step 3: Implement minimal robust monitoring and attribution**

Use rolling median/MAD with explicit behavior for zero MAD and insufficient history. Keep injected anomalies in tests only.

- [ ] **Step 4: Verify GREEN and full suite**

Run targeted tests, `pytest -q`, and `ruff check src scripts tests`.

Expected: all checks pass.

- [ ] **Step 5: Commit**

Commit message: `feat: detect and attribute KPI anomalies`.

### Task 7: Customer, cohort, seller, and delivery diagnostics

**Files:**
- Create: `growthlens/dbt/models/marts/commerce/mart_customer_cohorts.sql`
- Create: `growthlens/dbt/models/marts/commerce/mart_customer_rfm.sql`
- Create: `growthlens/dbt/models/marts/commerce/mart_seller_scorecard.sql`
- Create: `growthlens/dbt/models/marts/commerce/mart_delivery_diagnostics.sql`
- Create: `growthlens/tests/integration/test_commerce_diagnostics.py`
- Create: `growthlens/notebooks/01_commerce_eda.ipynb`
- Create: `growthlens/notebooks/02_root_cause_analysis.ipynb`

**Interfaces:**
- Consumes: commerce facts and dimensions from Task 5.
- Produces: stable analytical marts for cohort retention, transparent RFM scoring, seller priority, and delivery/review associations.

- [ ] **Step 1: Write failing diagnostic mart tests**

Assert first-purchase cohort assignment, month offsets, repeat behavior, RFM bin boundaries, seller minimum-volume rules, negative early-delivery days, and non-causal labeling of adjusted associations.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/integration/test_commerce_diagnostics.py -v`.

Expected: missing relations.

- [ ] **Step 3: Implement marts and thin reproducible notebooks**

Keep business calculations in SQL/Python modules; notebooks call those interfaces and explain results rather than hiding critical logic in cells.

- [ ] **Step 4: Execute notebooks and verify GREEN**

Run targeted tests, `dbt build`, notebook execution, and `pytest -q`.

Expected: all pass with saved outputs free of local absolute paths.

- [ ] **Step 5: Commit**

Commit message: `feat: add customer and operations diagnostics`.

### Task 8: Experiment validity and pre-analysis contract

**Files:**
- Create: `growthlens/dbt/models/marts/experiments/dim_experiment_customers.sql`
- Create: `growthlens/dbt/models/marts/experiments/fct_experiment_assignments.sql`
- Create: `growthlens/dbt/models/marts/experiments/fct_experiment_outcomes.sql`
- Create: `growthlens/dbt/models/marts/experiments/mart_experiment_quality.sql`
- Create: `growthlens/src/growthlens/experimentation.py`
- Create: `growthlens/reports/experiment_analysis_contract.md`
- Create: `growthlens/tests/test_experiment_validity.py`

**Interfaces:**
- Consumes: `stg_hillstrom_customers` from Task 4.
- Produces: `SampleRatioResult`, `BalanceResult`, `sample_ratio_test(observed: Mapping[str, int], expected: Mapping[str, float]) -> SampleRatioResult`, `standardized_mean_differences(frame: pd.DataFrame, group_col: str, covariates: Sequence[str], reference: str) -> pd.DataFrame`, and a frozen analysis contract naming conversion as primary.

- [ ] **Step 1: Write failing validity tests**

Cover a valid three-way split, deliberate SRM, shares not summing to one, duplicate customer assignment, missing groups, balanced and imbalanced covariates, and prohibition of `visit`, `conversion`, or `spend` as adjustment covariates.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_experiment_validity.py -v`.

Expected: missing experiment interfaces.

- [ ] **Step 3: Write and freeze the analysis contract before effect output**

Specify primary outcome, secondary outcomes, two treatment-versus-control comparisons, Holm correction family, confidence level, bootstrap seed, CUPED covariates, and exploratory subgroup policy.

- [ ] **Step 4: Implement validity functions and experiment marts**

The implementation must reject invalid expected shares and post-treatment adjustment variables with actionable messages.

- [ ] **Step 5: Verify GREEN and full suite**

Run targeted tests, `dbt build`, `pytest -q`, and Ruff.

Expected: all pass.

- [ ] **Step 6: Commit**

Commit message: `feat: validate randomized experiments`.

### Task 9: Treatment effects, multiplicity, CUPED, and segmentation

**Files:**
- Modify: `growthlens/src/growthlens/experimentation.py`
- Create: `growthlens/tests/test_experiment_effects.py`
- Create: `growthlens/notebooks/03_experiment_validation.ipynb`
- Create: `growthlens/notebooks/04_experiment_effects.ipynb`
- Create: `growthlens/dbt/models/marts/experiments/mart_experiment_summary.sql`
- Create: `growthlens/dbt/models/marts/experiments/mart_experiment_segments.sql`

**Interfaces:**
- Consumes: Task 8 validity results and experiment marts.
- Produces: `EffectEstimate`, `proportion_effect(...) -> EffectEstimate`, `bootstrap_mean_effect(...) -> EffectEstimate`, `holm_adjust(p_values: Sequence[float]) -> np.ndarray`, `cuped_adjust(outcome: ArrayLike, covariate: ArrayLike) -> np.ndarray`, and `interaction_effects(...) -> pd.DataFrame`.

- [ ] **Step 1: Write failing effect tests**

Use deterministic synthetic samples for zero effect, known positive effect, heavy zero-inflated spend, Holm ordering, variance-reducing CUPED, constant covariate, missing values, and subgroup interactions with minimum sample guards.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_experiment_effects.py -v`.

Expected: missing functions or attributes.

- [ ] **Step 3: Implement minimal effect estimators**

Return absolute and relative effects, confidence intervals, raw and adjusted p-values, sample sizes, and method labels. Keep uplift modeling out of the required first release unless all core deliverables are green.

- [ ] **Step 4: Execute Hillstrom analysis and verify outputs**

Run targeted tests, notebook execution, and `pytest -q`.

Expected: deterministic outputs matching the frozen analysis contract.

- [ ] **Step 5: Commit**

Commit message: `feat: estimate experiment treatment effects`.

### Task 10: Verified metric artifacts and decision reporting

**Files:**
- Create: `growthlens/src/growthlens/reporting.py`
- Create: `growthlens/scripts/build_artifacts.py`
- Create: `growthlens/tests/test_reporting.py`
- Create: `growthlens/artifacts/.gitkeep`
- Create: `growthlens/reports/executive_decision_memo.md`
- Create: `growthlens/reports/experiment_readout.md`
- Create: `growthlens/reports/data_dictionary.md`
- Create: `growthlens/reports/limitations.md`

**Interfaces:**
- Consumes: commerce marts, monitoring alerts, validity results, and treatment effects.
- Produces: `build_verified_metrics(...) -> dict[str, JSONValue]`, `write_verified_metrics(path: Path, metrics: Mapping[str, JSONValue]) -> None`, `artifacts/verified_metrics.json`, and `artifacts/run_manifest.json`.

- [ ] **Step 1: Write failing reporting tests**

Assert stable JSON ordering, schema version, source/run provenance, rejection of NaN/Infinity, explicit `analysis_type` labels, confidence intervals, and separation of observed results from scenario assumptions.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_reporting.py -v`.

Expected: import failure for `growthlens.reporting`.

- [ ] **Step 3: Implement artifact generation**

Generate machine-readable metrics and run metadata from database queries and statistical outputs; reports must cite artifact keys rather than hand-typed values.

- [ ] **Step 4: Build and reconcile artifacts**

Run artifact generation twice and compare hashes after removing run timestamps; run `pytest -q` and Ruff.

Expected: deterministic analytical values and all tests pass.

- [ ] **Step 5: Commit**

Commit message: `feat: generate verified analytics reports`.

### Task 11: Power BI semantic model and five-page dashboard

**Files:**
- Create: `growthlens/powerbi/model.md`
- Create: `growthlens/powerbi/measures.md`
- Create: `growthlens/powerbi/theme.json`
- Create: `growthlens/powerbi/GrowthLens.pbix`
- Create: `growthlens/powerbi/screenshots/`
- Create: `growthlens/powerbi/GrowthLens-dashboard.pdf`
- Create: `growthlens/scripts/export_powerbi_inputs.py`
- Create: `growthlens/tests/test_powerbi_exports.py`

**Interfaces:**
- Consumes: stable marts and `verified_metrics.json` from Tasks 5-10.
- Produces: star-schema documentation, DAX measures, deterministic dashboard input extracts, a five-page PBIX, screenshots, and PDF.

- [ ] **Step 1: Write failing export reconciliation tests**

Assert every dashboard table has a declared grain and key, export values match SQL fixture values, filenames are stable, and no raw customer identifiers enter the BI layer.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_powerbi_exports.py -v`.

Expected: missing export module and files.

- [ ] **Step 3: Implement deterministic Power BI input exports and DAX specification**

Produce only the minimum tables needed by the five specified pages. Document relationships, filter direction, formats, and every DAX formula.

- [ ] **Step 4: Build the PBIX and export visual evidence**

Use Power BI Desktop to create Management Overview, Revenue and Customer Growth, Fulfillment and Seller Operations, Experiment Decision, and Data Quality pages. Export screenshots and PDF.

- [ ] **Step 5: Reconcile and visually inspect**

Run export tests and full suite; compare dashboard KPI cards to `verified_metrics.json`; inspect every page for clipping, incorrect filters, misleading axes, and unreadable labels.

- [ ] **Step 6: Commit**

Commit message: `feat: add Power BI decision dashboard`.

### Task 12: End-to-end reproducibility, CI, and portfolio documentation

**Files:**
- Create: `growthlens/.github/workflows/ci.yml`
- Create: `growthlens/scripts/run_pipeline.py`
- Create: `growthlens/tests/test_pipeline.py`
- Create: `growthlens/tests/test_notebook_hygiene.py`
- Modify: `growthlens/README.md`
- Modify: `growthlens/Makefile`
- Create: `growthlens/docs/architecture.md`
- Create: `growthlens/docs/interview-guide.md`
- Create: `growthlens/docs/resume-evidence.md`

**Interfaces:**
- Consumes: every prior task's public interface.
- Produces: `run_pipeline(stages: Sequence[str], settings: Settings) -> PipelineResult`, CI checks, complete reproduction instructions, architecture diagrams, interview narrative, and evidence-only resume drafting inputs.

- [ ] **Step 1: Write failing orchestration and hygiene tests**

Assert stage order, stop-on-quality-failure, rerun idempotency, helpful failure messages, notebooks without absolute paths or hidden state, and README commands that reference existing targets.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_pipeline.py tests/test_notebook_hygiene.py -v`.

Expected: missing pipeline interface or failed documentation contracts.

- [ ] **Step 3: Implement pipeline orchestration and CI**

Provide separate `verify`, `build`, and `report` commands; CI uses fixture data and does not require Kaggle credentials or Power BI.

- [ ] **Step 4: Run a clean-room reproduction**

From a clean virtual environment and fresh PostgreSQL volume, run the documented fixture pipeline, full tests, lint, dbt build, and notebook execution.

Expected: all automated checks pass without local-only paths or secrets.

- [ ] **Step 5: Commit**

Commit message: `docs: make GrowthLens reproducible and interview ready`.

### Task 13: Public-repository safety audit and GitHub publication

**Files:**
- Create: `growthlens/tests/test_repository_hygiene.py`
- Create: `growthlens/NOTICE.md`
- Modify: `growthlens/LICENSE`
- Modify: `growthlens/README.md`
- Modify: `growthlens/.gitignore`

**Interfaces:**
- Consumes: complete repository and verified artifacts.
- Produces: a clean public Git history and a public GitHub repository with the local `origin` remote configured.

- [ ] **Step 1: Write failing repository hygiene tests**

Reject raw CSV/Parquet archives, `.env`, credentials, database files, absolute local user paths, phone numbers, private email addresses, and oversized generated files outside the approved Power BI artifacts.

- [ ] **Step 2: Verify RED against an intentional forbidden fixture**

Run: `pytest tests/test_repository_hygiene.py -v`.

Expected: the intentional forbidden fixture is detected; remove it only after the test proves detection.

- [ ] **Step 3: Implement repository policy and attribution**

Add licensing, dataset notices, third-party references, public-data limitations, and a clear distinction between project analysis and employment experience.

- [ ] **Step 4: Run final local verification**

Run: `pytest -q`, `ruff check src scripts tests`, `dbt build`, notebook execution, artifact reconciliation, repository hygiene tests, and a secret scanner over the full Git history.

Expected: all checks pass with no secrets, raw datasets, personal information, or unverified resume metrics.

- [ ] **Step 5: Merge the implementation branch locally**

Use the finishing-development-branch workflow to integrate `codex/initial-implementation` into `main` after final review.

- [ ] **Step 6: Create and push the public GitHub repository**

Create a public repository named `growthlens`, set `origin`, push `main`, and verify the remote README, screenshots, license, and latest commit. Do not publish if the privacy audit differs locally and remotely.

- [ ] **Step 7: Record the publication**

Add the verified GitHub URL to `docs/resume-evidence.md`, commit, push, and confirm the remote commit SHA matches local `main`.

## Plan Self-Review Record

- Spec coverage: all eighteen design sections map to Tasks 1-13; optional uplift modeling remains explicitly outside the required first release.
- Step scan: behavior tasks follow RED-GREEN verification; configuration and documentation are attached to consuming behavior and validation.
- Type consistency: `Settings`, dataset contracts, ingestion manifest, monitoring alerts, experiment result types, verified metrics, and pipeline result flow forward through named interfaces.
- Review focus: each of the five highest-risk input classes has a named test in its owning task.
- Proportion: the plan fixes interfaces, verification commands, and task boundaries without prescribing implementation bodies.
