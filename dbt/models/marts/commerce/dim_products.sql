select
    products.product_id,
    products.product_category_name,
    translation.product_category_name_english,
    products.product_name_length,
    products.product_description_length,
    products.product_photo_count,
    products.product_weight_g,
    products.product_length_cm,
    products.product_height_cm,
    products.product_width_cm
from {{ ref('stg_olist_products') }} products
left join {{ ref('stg_olist_category_translation') }} translation
    on products.product_category_name = translation.product_category_name
