select
    items.order_id,
    items.order_item_id,
    items.product_id,
    items.seller_id,
    items.shipping_limit_at,
    items.item_value,
    items.freight_value,
    orders.purchased_at,
    orders.order_status,
    orders.is_commercial_order
from {{ ref('stg_olist_order_items') }} items
inner join {{ ref('int_order_enriched') }} orders
    on items.order_id = orders.order_id
