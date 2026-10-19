select order_id, payment_sequence
from {{ ref('stg_olist_order_payments') }}
group by 1, 2
having count(*) > 1
