select
    order_id,
    order_status,
    order_status not in ('canceled', 'unavailable') as is_commercial_order
from {{ ref('stg_olist_orders') }}
