# DAX measure catalog

All currency measures use Brazilian real (`R$`). Percentages use one decimal
place. A blank denominator stays blank rather than being silently converted to
zero.

```DAX
Merchandise Value = SUM('Daily KPI'[merchandise_value])

Freight Value = SUM('Daily KPI'[freight_value])

Payment Value = SUM('Daily KPI'[payment_value])

Orders = SUM('Daily KPI'[orders])

Customers = SUM('Daily KPI'[customers])

Average Order Value = DIVIDE([Merchandise Value], [Orders])

Repeat Customer Rate =
DIVIDE(
    SUMX('Daily KPI', 'Daily KPI'[repeat_customer_rate] * 'Daily KPI'[customers]),
    [Customers]
)

On-time Delivery Rate =
DIVIDE(
    SUMX('Daily KPI', 'Daily KPI'[on_time_delivery_rate] * 'Daily KPI'[orders]),
    [Orders]
)

Average Review Score =
DIVIDE(
    SUMX('Daily KPI', 'Daily KPI'[average_review_score] * 'Daily KPI'[orders]),
    [Orders]
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

Duplicate Assignment Count = SUM('Experiment Quality'[duplicate_customer_count])
```

Experiment confidence intervals and Holm-adjusted p-values are imported from
`artifacts/verified_metrics.json`; they are never recomputed in DAX.
