with customer_months as (
    select
        customer_unique_id,
        cast(date_trunc('month', purchased_at) as date) as activity_month,
        count(*) as orders_in_month,
        sum(merchandise_value) as merchandise_value
    from {{ ref('fct_orders') }}
    where is_commercial_order
    group by customer_unique_id, cast(date_trunc('month', purchased_at) as date)
), assigned as (
    select
        *,
        min(activity_month) over (partition by customer_unique_id) as cohort_month
    from customer_months
)

select
    customer_unique_id,
    cohort_month,
    activity_month,
    (
        (extract(year from activity_month) - extract(year from cohort_month)) * 12
        + extract(month from activity_month) - extract(month from cohort_month)
    )::integer as month_offset,
    orders_in_month,
    merchandise_value,
    activity_month > cohort_month as is_repeat_activity
from assigned
