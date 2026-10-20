# Experiment Decision Lab — frozen analysis contract

Status: **frozen before treatment-effect estimation**.

## Design and estimands

- Population: all 64,000 rows in the public Hillstrom randomized email experiment after schema,
  stable source-row-key uniqueness, baseline-missingness, and outcome-domain checks. The file has
  no durable real-world customer identifier, so cross-row customer uniqueness is not asserted.
- Arms: `Mens E-Mail`, `Womens E-Mail`, and `No E-Mail` control.
- Primary outcome: binary `conversion` during the experiment window.
- Primary estimands: intention-to-treat risk difference for `Mens E-Mail` versus control and
  `Womens E-Mail` versus control.
- Secondary outcomes: binary `visit` and continuous `spend`, reported as secondary evidence and
  never substituted for the primary result.

## Inference frozen in advance

- Two-sided confidence level: 95%; family-wise alpha: 0.05.
- Primary comparison family: the two treatment-versus-control conversion tests.
- Multiplicity control: Holm step-down correction across that two-test primary family.
- Interval method: normal/Welch intervals for transparent point estimates, supplemented by a
  nonparametric percentile bootstrap for spend.
- Bootstrap: 5,000 replicates with seed `20261019`.
- CUPED covariates: `recency`, `history`, `mens`, `womens`, `newbie`; categorical baseline fields
  (`channel`, `zip_code`) may be used only in a separately labeled regression sensitivity model.
- Forbidden adjustment variables: `visit`, `conversion`, and `spend`, because they are measured
  after assignment.

## Validity gates

Effect output is blocked when any expected arm is missing, source-row keys repeat, expected
allocation shares are invalid, the sample-ratio-mismatch test rejects at 0.01, or the maximum
baseline `|SMD|` reaches 0.10. Baseline missingness is published as a diagnostic. The primary
effect estimates remain unadjusted; CUPED is implemented and tested as a sensitivity utility but
is not represented as part of the published result.

## Exploratory work

Subgroup estimates (channel, prior purchase category, recency band, history band) are exploratory.
They require interaction tests, minimum cell sizes, multiplicity labels, and shrinkage-aware
interpretation. A visually different subgroup point estimate is not described as heterogeneous
impact without an interaction result.
