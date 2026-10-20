with seller_orders as (
    select
        items.seller_id,
        items.order_id,
        sum(items.item_value) as merchandise_value,
        sum(items.freight_value) as freight_value,
        max(case when orders.is_late_delivery then 1 else 0 end) as late_delivery,
        max(orders.review_score) as review_score
    from {{ ref('fct_order_items') }} items
    inner join {{ ref('fct_orders') }} orders
        on items.order_id = orders.order_id
    where items.is_commercial_order
    group by items.seller_id, items.order_id
), seller_metrics as (
    select
        seller_id,
        count(*) as commercial_order_count,
        sum(merchandise_value) as merchandise_value,
        sum(freight_value) as freight_value,
        avg(cast(late_delivery as double precision)) as late_delivery_rate,
        avg(review_score) as average_review_score
    from seller_orders
    group by seller_id
)

select
    *,
    commercial_order_count >= 3 as is_priority_eligible,
    case
        when commercial_order_count >= 3 then
            0.6 * coalesce(late_delivery_rate, 0)
            + 0.4 * (1 - coalesce(average_review_score, 5) / 5.0)
        else null
    end as priority_score
from seller_metrics
