# GrowthLens interview guide

## 60-second project introduction

GrowthLens is my end-to-end data-analysis portfolio project. I used two independent public datasets:
Olist for commerce monitoring and Hillstrom for randomized experimentation. I first built file
contracts and audited idempotent ingestion, then used dbt to create grain-safe facts, dimensions,
and KPI marts. Python handles robust anomaly detection and experiment inference, while Power BI
consumes privacy-safe extracts. The important part is not only the dashboard: every headline number
can be traced to a source hash, load run, tested SQL model, and generated JSON artifact.

## Questions and evidence-backed answers

### How did you prevent SQL fan-out?

Orders have one-to-many items, payments, and reviews. Joining all raw tables directly multiplies
rows and inflates value. I aggregate each child relation to order grain first, keep child counts for
auditability, and then join those order-grain intermediates. A fixture with two items, two payments,
and duplicate reviews asserts exact merchandise, freight, payment, and review outputs.

### Why are there three monetary measures?

Merchandise value is item price, freight is shipping charge, and payment value is what payment
records total. Calling all three GMV would hide reconciliation differences. The metric catalog
freezes definitions, denominator, time field, and exclusions.

### Why is the on-time rate 91.89% rather than an average of daily percentages?

The reported figure sums on-time eligible orders and divides by all eligible delivered orders.
This avoids giving a low-volume day the same weight as a high-volume day. The daily mart exposes
both numerator and denominator, and the artifact generator recomputes the overall rate from them.

### What validates the randomized experiment?

The analysis contract was frozen before effects: conversion is primary, the two email groups are
each compared with no-email control, p-values use Holm adjustment, intervals are 95%, and
post-treatment variables are prohibited from adjustment. The assignment counts are balanced
(SRM p = 0.9037) with zero duplicate assignments.

### What do the effects mean?

Men's email increases conversion by 0.68 percentage points (95% CI 0.50 to 0.86); women's email by
0.31 points (95% CI 0.15 to 0.47). These are absolute effects, not relative lift. Both survive the
two-comparison Holm correction. Operational rollout would still require message cost, unsubscribe,
and long-term guardrails that are absent from the public dataset.

### Why not claim delivery delays caused poor reviews?

Olist delivery was not randomized. The observed late/on-time review difference can prioritize
investigation but may be confounded by product, seller, distance, or service recovery. The model
and dashboard explicitly label it `associational_not_causal`.

### How is rerunning safe?

Each row has a deterministic hash; reloading the same files inserts zero new business rows while
adding a new audit attempt. The pipeline stages run in fixed order and stop on the first quality
failure. CI runs unit, integration, statistical, notebook-hygiene, dbt, and repository-hygiene gates.

## Likely deep dives

- Explain `customer_order_id` versus `customer_unique_id` in Olist.
- Derive the difference-in-proportions standard error and confidence interval.
- Explain why a statistically significant effect may not be commercially worthwhile.
- Compare rolling mean/z-score monitoring with median/MAD under outliers.
- Describe how you would add incremental models, snapshots, orchestration, and access controls.
- Show one failing test that prevented a misleading metric.

## Honest limitations

- Public historical data is not a live production feed.
- Olist is an order lifecycle dataset, not a clickstream funnel.
- The experiment lacks modern messaging guardrails and cost data.
- Seller scoring is a transparent prioritization heuristic, not a causal risk score.
- The checked-in Power BI artifact is PBIP/TMDL source plus PDF evidence; creating a binary PBIX
  requires Power BI Desktop.
