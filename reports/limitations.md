# Limitations and truth boundaries

- Olist and Hillstrom are independent public datasets and are never joined or described as one
  employer's system.
- Olist records order lifecycle timestamps, not website clickstream events; the project does not
  claim page-view conversion funnels.
- Marketplace records cover the published historical window and are not evidence of current
  company performance.
- Delivery timing and review-score results are observational associations vulnerable to product,
  geography, seller, and customer-mix confounding.
- Hillstrom supports randomized email effects in its original experiment population; transport to
  another company or current market requires new evidence.
- Subgroup estimates are exploratory and can be noisy even after minimum-cell guards.
- Scenario annualization, cost, and rollout assumptions live only under `scenario_assumptions` and
  are never presented as observed impact.
- Resume metrics may be copied only from a committed, reproducible `verified_metrics.json` whose
  hash matches `run_manifest.json`.
