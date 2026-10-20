# Analytical data dictionary

| Relation | Grain | Purpose |
|---|---|---|
| `marts.fct_orders` | One row per Olist order | Reconciled item, freight, payment, delivery, and review measures |
| `marts.fct_order_items` | One row per order item | Product and seller analysis without payment/review fan-out |
| `marts.mart_daily_kpis` | Purchase date | Governed operating KPI series |
| `marts.mart_customer_cohorts` | Customer and active month | First-month cohort and repeat activity |
| `marts.mart_customer_rfm` | Person-level customer | Fixed-boundary RFM scoring |
| `marts.mart_seller_scorecard` | Seller | Volume-gated operational triage |
| `marts.mart_delivery_diagnostics` | Delivered order | Non-causal delivery/review association inputs |
| `marts.fct_experiment_assignments` | Experiment row | Randomized arm assignment |
| `marts.fct_experiment_outcomes` | Experiment row | Visit, conversion, and spend outcomes |
| `marts.mart_experiment_summary` | Experiment arm | Descriptive arm outcomes |

Column-level business definitions for headline commerce metrics are frozen in
`reports/metric_catalog.md`; experimental estimands are frozen in
`reports/experiment_analysis_contract.md`.
