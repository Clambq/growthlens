with long_metrics as (
    select metric_date, 'merchandise_value' as metric, cast(merchandise_value as double precision) as actual
    from {{ ref('mart_daily_kpis') }}
    union all
    select metric_date, 'orders', cast(orders as double precision)
    from {{ ref('mart_daily_kpis') }}
    union all
    select metric_date, 'average_order_value', cast(average_order_value as double precision)
    from {{ ref('mart_daily_kpis') }}
    union all
    select metric_date, 'on_time_delivery_rate', cast(on_time_delivery_rate as double precision)
    from {{ ref('mart_daily_kpis') }}
), baselines as (
    select
        *,
        avg(actual) over (
            partition by metric order by metric_date
            rows between 28 preceding and 1 preceding
        ) as trailing_mean,
        stddev_samp(actual) over (
            partition by metric order by metric_date
            rows between 28 preceding and 1 preceding
        ) as trailing_stddev
    from long_metrics
)

select
    *,
    (actual - trailing_mean) / nullif(trailing_stddev, 0) as diagnostic_z_score,
    case
        when abs((actual - trailing_mean) / nullif(trailing_stddev, 0)) >= 3 then true
        else false
    end as is_diagnostic_alert
from baselines
