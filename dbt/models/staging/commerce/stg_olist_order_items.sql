select
    cast(order_id as varchar) as order_id,
    cast(order_item_id as integer) as order_item_id,
    cast(product_id as varchar) as product_id,
    cast(seller_id as varchar) as seller_id,
    cast(nullif(cast(shipping_limit_date as varchar), '') as timestamp) as shipping_limit_at,
    cast(price as decimal(18, 2)) as item_value,
    cast(freight_value as decimal(18, 2)) as freight_value,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'order_items') }}
