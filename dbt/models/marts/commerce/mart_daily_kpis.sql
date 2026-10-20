select
    cast(purchased_at as date) as metric_date,
    sum(merchandise_value) as merchandise_value,
    sum(freight_value) as freight_value,
    sum(payment_value) as payment_value,
    count(*) as orders,
    count(distinct customer_unique_id) as customers,
    cast(sum(merchandise_value) as double precision) / nullif(count(*), 0)
        as average_order_value,
    cast(
        count(distinct case when customer_commercial_order_number > 1 then customer_unique_id end)
        as double precision
    ) / nullif(count(distinct customer_unique_id), 0) as repeat_customer_rate,
    cast(
        sum(
            case
                when delivered_at is not null
                    and estimated_delivery_at is not null
                    and delivered_at <= estimated_delivery_at then 1
                else 0
            end
        ) as double precision
    ) / nullif(
        sum(
            case
                when delivered_at is not null and estimated_delivery_at is not null then 1
                else 0
            end
        ),
        0
    ) as on_time_delivery_rate,
    avg(review_score) as average_review_score
    , sum(
        case
            when delivered_at is not null and estimated_delivery_at is not null then 1
            else 0
        end
    ) as eligible_delivery_orders
    , sum(
        case
            when delivered_at is not null
                and estimated_delivery_at is not null
                and delivered_at <= estimated_delivery_at then 1
            else 0
        end
    ) as on_time_delivery_orders
    , sum(case when review_score is not null then 1 else 0 end) as reviewed_orders
    , sum(coalesce(review_score, 0)) as review_score_total
from {{ ref('int_order_enriched') }}
where is_commercial_order
group by cast(purchased_at as date)
