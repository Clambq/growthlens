# Experiment readout

Source of truth: `artifacts/verified_metrics.json`.

1. Check `observed_results.experiment.sample_ratio_p_value.value` before effects.
2. Compare the two `*_conversion_effect.value` risk differences.
3. Read each `confidence_interval` and `holm_adjusted_p_value`; do not use the raw p-value alone.
4. Treat visit and spend as secondary outcomes under the frozen contract.
5. Treat all segment cuts as exploratory unless an interaction test and minimum-cell guard pass.

The artifact records absolute effects. Relative lift may be added as a labeled companion metric,
but it must never replace the absolute risk difference.
