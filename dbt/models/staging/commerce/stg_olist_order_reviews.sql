select
    cast(review_id as varchar) as review_id,
    cast(order_id as varchar) as order_id,
    cast(review_score as integer) as review_score,
    cast(review_comment_title as varchar) as review_comment_title,
    cast(review_comment_message as varchar) as review_comment_message,
    cast(nullif(cast(review_creation_date as varchar), '') as timestamp) as review_created_at,
    cast(nullif(cast(review_answer_timestamp as varchar), '') as timestamp) as review_answered_at,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'order_reviews') }}
