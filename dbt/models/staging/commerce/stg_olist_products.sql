select
    cast(product_id as varchar) as product_id,
    cast(product_category_name as varchar) as product_category_name,
    cast(nullif(cast(product_name_lenght as varchar), '') as integer) as product_name_length,
    cast(nullif(cast(product_description_lenght as varchar), '') as integer) as product_description_length,
    cast(nullif(cast(product_photos_qty as varchar), '') as integer) as product_photo_count,
    cast(nullif(cast(product_weight_g as varchar), '') as decimal(18, 2)) as product_weight_g,
    cast(nullif(cast(product_length_cm as varchar), '') as decimal(18, 2)) as product_length_cm,
    cast(nullif(cast(product_height_cm as varchar), '') as decimal(18, 2)) as product_height_cm,
    cast(nullif(cast(product_width_cm as varchar), '') as decimal(18, 2)) as product_width_cm,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'products') }}
