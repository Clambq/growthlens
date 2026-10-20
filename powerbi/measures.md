# DAX measure catalog

All currency measures use Brazilian real (`R$`). Percentages use one decimal
place. A blank denominator stays blank rather than being silently converted to
zero.

```DAX
Merchandise Value = SUM('Daily KPI'[merchandise_value])

Freight Value = SUM('Daily KPI'[freight_value])

Payment Value = SUM('Daily KPI'[payment_value])

Orders = SUM('Daily KPI'[orders])

Customers = MAX('Customer Summary'[unique_customers])

Average Order Value = DIVIDE([Merchandise Value], [Orders])

Repeat Customer Rate = MAX('Customer Summary'[repeat_customer_rate])

On-time Delivery Rate =
DIVIDE(
    SUM('Daily KPI'[on_time_delivery_orders]),
    SUM('Daily KPI'[eligible_delivery_orders])
)

Average Review Score =
DIVIDE(
    SUM('Daily KPI'[review_score_total]),
    SUM('Daily KPI'[reviewed_orders])
)

Late Delivery Rate =
DIVIDE(
    CALCULATE(SUM('Delivery Summary'[delivered_orders]), 'Delivery Summary'[is_late_delivery] = TRUE()),
    SUM('Delivery Summary'[delivered_orders])
)

Experiment Customers = SUM('Experiment Summary'[customers])

Conversion Rate =
DIVIDE(
    SUMX('Experiment Summary', 'Experiment Summary'[conversion_rate] * 'Experiment Summary'[customers]),
    [Experiment Customers]
)

Conversion Lift vs Control =
VAR SelectedRate = [Conversion Rate]
VAR ControlRate =
    CALCULATE(
        [Conversion Rate],
        REMOVEFILTERS('Dim Experiment Segment'),
        'Dim Experiment Segment'[segment] = "No E-Mail"
    )
RETURN SelectedRate - ControlRate

Duplicate Source Row Key Count = MAX('Experiment Quality'[duplicate_source_row_key_count])
```

Experiment confidence intervals and Holm-adjusted p-values are imported from
`artifacts/verified_metrics.json`; they are never recomputed in DAX.
