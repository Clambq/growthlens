select
    order_id,
    count(*) as item_count,
    sum(item_value) as merchandise_value,
    sum(freight_value) as freight_value
from {{ ref('stg_olist_order_items') }}
group by order_id
