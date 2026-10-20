select
    order_id,
    customer_unique_id,
    cast(purchased_at as date) as purchase_date,
    cast(delivered_at as date) - cast(purchased_at as date) as delivery_days,
    cast(delivered_at as date) - cast(estimated_delivery_at as date) as delivery_delay_days,
    is_late_delivery,
    review_score,
    merchandise_value,
    'associational_not_causal' as interpretation_label
from {{ ref('fct_orders') }}
where is_commercial_order
  and delivered_at is not null
  and estimated_delivery_at is not null
