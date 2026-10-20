select
    order_id,
    count(*) as payment_count,
    sum(payment_value) as payment_value
from {{ ref('stg_olist_order_payments') }}
group by order_id
