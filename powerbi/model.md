# GrowthLens Power BI semantic model

The BI layer consumes six deterministic extracts produced by
`scripts/export_powerbi_inputs.py`. Olist commerce and Hillstrom experiment
tables remain separate analytical cases. They share a report shell, not entity
relationships.

| Table | Grain | Key | Purpose |
| --- | --- | --- | --- |
| Daily KPI | purchase date | `metric_date` | executive and growth trends |
| Customer Cohort | cohort month x activity month | `cohort_month`, `activity_month` | retention and repeat activity |
| Delivery Summary | purchase date x late-delivery flag | `purchase_date`, `is_late_delivery` | fulfillment and review association |
| Seller Scorecard | pseudonymous seller | `seller_key` | seller prioritization |
| Experiment Summary | randomized segment | `segment` | outcome comparison |
| Experiment Quality | randomized segment | `segment` | assignment checks |

## Relationships

- `Dim Date[Date]` 1:* `Daily KPI[metric_date]`, single direction.
- `Dim Date[Date]` 1:* `Delivery Summary[purchase_date]`, single direction.
- `Dim Experiment Segment[segment]` 1:1 `Experiment Summary[segment]`, single direction.
- `Dim Experiment Segment[segment]` 1:1 `Experiment Quality[segment]`, single direction.
- Customer cohorts use their two month fields directly so the acquisition and
  activity roles cannot be confused by an implicit date relationship.
- Seller scorecard is intentionally disconnected and filtered only by its own
  eligibility/status fields.

The export contract prevents raw customer, order, and seller identifiers from
entering the BI layer. `seller_key` is a stable SHA-256-derived pseudonym.

## Report pages

1. **Management Overview** - headline commerce KPIs, trends, and latest quality state.
2. **Revenue and Customer Growth** - merchandise value, AOV, customers, repeat rate, and cohorts.
3. **Fulfillment and Seller Operations** - delivery latency, late-rate/review association, and seller priorities.
4. **Experiment Decision** - randomized conversion effects, intervals, multiplicity status, and segment outcomes.
5. **Data Quality** - source runs, row counts, assignment balance, duplicate checks, and caveats.

The checked-in `.pbip` source is the editable artifact. Open `GrowthLens.pbip`
in Power BI Desktop and save as `GrowthLens.pbix` when a binary handoff is
required. Binary PBIX files are not fabricated on machines without Power BI
Desktop.
