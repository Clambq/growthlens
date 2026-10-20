select
    order_id,
    count(*) as review_count,
    avg(review_score) as review_score
from {{ ref('stg_olist_order_reviews') }}
group by order_id
