select order_id, order_item_id
from {{ ref('stg_olist_order_items') }}
group by 1, 2
having count(*) > 1
