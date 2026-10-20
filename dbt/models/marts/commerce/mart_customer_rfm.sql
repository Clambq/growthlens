with customer_metrics as (
    select
        customer_unique_id,
        max(cast(purchased_at as date)) as latest_order_date,
        count(*) as frequency,
        sum(merchandise_value) as monetary_value
    from {{ ref('fct_orders') }}
    where is_commercial_order
    group by customer_unique_id
), as_of as (
    select max(latest_order_date) as analysis_date
    from customer_metrics
), scored as (
    select
        metrics.*,
        as_of.analysis_date,
        cast(as_of.analysis_date - metrics.latest_order_date as integer) as recency_days
    from customer_metrics metrics
    cross join as_of
)

select
    *,
    case
        when recency_days <= 30 then 5
        when recency_days <= 60 then 4
        when recency_days <= 90 then 3
        when recency_days <= 180 then 2
        else 1
    end as recency_score,
    case
        when frequency >= 5 then 5
        when frequency = 4 then 4
        when frequency = 3 then 3
        when frequency = 2 then 2
        else 1
    end as frequency_score,
    case
        when monetary_value >= 1000 then 5
        when monetary_value >= 500 then 4
        when monetary_value >= 250 then 3
        when monetary_value >= 100 then 2
        else 1
    end as monetary_score
from scored
