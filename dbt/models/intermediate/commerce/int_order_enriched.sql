with base as (
    select
        orders.order_id,
        orders.customer_order_id,
        customers.customer_unique_id,
        orders.order_status,
        scope.is_commercial_order,
        orders.purchased_at,
        orders.approved_at,
        orders.carrier_received_at,
        orders.delivered_at,
        orders.estimated_delivery_at,
        orders.has_invalid_timestamp_order,
        orders.is_late_delivery,
        coalesce(items.item_count, 0) as item_count,
        coalesce(items.merchandise_value, 0) as merchandise_value,
        coalesce(items.freight_value, 0) as freight_value,
        coalesce(payments.payment_count, 0) as payment_count,
        coalesce(payments.payment_value, 0) as payment_value,
        coalesce(reviews.review_count, 0) as review_count,
        reviews.review_score
    from {{ ref('stg_olist_orders') }} orders
    inner join {{ ref('stg_olist_customers') }} customers
        on orders.customer_order_id = customers.customer_order_id
    inner join {{ ref('int_order_scope') }} scope
        on orders.order_id = scope.order_id
    left join {{ ref('int_order_item_agg') }} items
        on orders.order_id = items.order_id
    left join {{ ref('int_order_payment_agg') }} payments
        on orders.order_id = payments.order_id
    left join {{ ref('int_order_review_agg') }} reviews
        on orders.order_id = reviews.order_id
), sequenced as (
    select
        *,
        case
            when is_commercial_order then
                sum(case when is_commercial_order then 1 else 0 end) over (
                    partition by customer_unique_id
                    order by purchased_at, order_id
                    rows between unbounded preceding and current row
                )
            else null
        end as customer_commercial_order_number
    from base
)

select * from sequenced
