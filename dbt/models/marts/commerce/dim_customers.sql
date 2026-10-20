select
    customers.customer_unique_id,
    min(customers.customer_city) as customer_city,
    min(customers.customer_state) as customer_state,
    min(orders.purchased_at) as first_order_at,
    max(orders.purchased_at) as latest_order_at,
    sum(case when orders.is_commercial_order then 1 else 0 end) as commercial_order_count
from {{ ref('stg_olist_customers') }} customers
left join {{ ref('int_order_enriched') }} orders
    on customers.customer_order_id = orders.customer_order_id
group by customers.customer_unique_id
