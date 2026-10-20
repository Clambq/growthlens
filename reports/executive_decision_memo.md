# Executive decision memo

This memo is intentionally value-free in source control: every displayed number must be rendered
from `artifacts/verified_metrics.json`, never copied by hand.

## Commerce operating view

- Order volume: `observed_results.commerce.orders.value`
- Merchandise value (freight excluded): `observed_results.commerce.merchandise_value.value`
- On-time delivery rate: `observed_results.commerce.on_time_delivery_rate.value`
- Average review score: `observed_results.commerce.average_review_score.value`

Recommended workflow: inspect a detected KPI change, attribute it by geography/category/seller,
then validate operational records before recommending intervention. Delivery/review relationships
remain associational.

## Experiment decision view

The email recommendation is based on the two Holm-adjusted conversion effects under
`observed_results.experiment`. A rollout recommendation requires the confidence interval,
adjusted p-value, sample-ratio gate, operational cost, and guardrail review together.
