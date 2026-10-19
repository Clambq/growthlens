with typed as (
    select
        cast(order_id as varchar) as order_id,
        cast(customer_id as varchar) as customer_order_id,
        lower(trim(cast(order_status as varchar))) as order_status,
        cast(nullif(cast(order_purchase_timestamp as varchar), '') as timestamp) as purchased_at,
        cast(nullif(cast(order_approved_at as varchar), '') as timestamp) as approved_at,
        cast(nullif(cast(order_delivered_carrier_date as varchar), '') as timestamp) as carrier_received_at,
        cast(nullif(cast(order_delivered_customer_date as varchar), '') as timestamp) as delivered_at,
        cast(nullif(cast(order_estimated_delivery_date as varchar), '') as timestamp) as estimated_delivery_at,
        cast(_loaded_at as timestamp) as loaded_at
    from {{ source('raw', 'orders') }}
)

select
    *,
    case
        when approved_at < purchased_at then true
        when carrier_received_at < approved_at then true
        when delivered_at < carrier_received_at then true
        else false
    end as has_invalid_timestamp_order,
    case
        when delivered_at is not null and estimated_delivery_at is not null
            then delivered_at > estimated_delivery_at
        else null
    end as is_late_delivery
from typed
