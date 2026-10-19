select
    cast(order_id as varchar) as order_id,
    cast(payment_sequential as integer) as payment_sequence,
    lower(trim(cast(payment_type as varchar))) as payment_type,
    cast(payment_installments as integer) as payment_installments,
    cast(payment_value as decimal(18, 2)) as payment_value,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'order_payments') }}
