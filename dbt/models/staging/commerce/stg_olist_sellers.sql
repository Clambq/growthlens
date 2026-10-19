select
    cast(seller_id as varchar) as seller_id,
    cast(seller_zip_code_prefix as varchar) as seller_zip_code_prefix,
    lower(trim(cast(seller_city as varchar))) as seller_city,
    upper(trim(cast(seller_state as varchar))) as seller_state,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'sellers') }}
