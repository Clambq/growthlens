select
    cast(product_category_name as varchar) as product_category_name,
    cast(product_category_name_english as varchar) as product_category_name_english,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'category_translation') }}
