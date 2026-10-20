# GrowthLens metric catalog

The catalog freezes metric meaning before dashboarding. Olist lifecycle timestamps represent
operational order states; they are not interpreted as page-view or clickstream funnel events.

| Metric | Grain | Numerator / calculation | Denominator | Inclusion and exclusions |
|---|---|---|---|---|
| `merchandise_value` | Order, day | Sum of `order_items.price` | None | Excludes freight. Daily values exclude `canceled` and `unavailable` orders. |
| `freight_value` | Order, day | Sum of `order_items.freight_value` | None | Kept separate from merchandise value. Same status scope as above. |
| `payment_value` | Order, day | Sum of all payment records | None | Not called GMV. Same status scope as above. |
| `orders` | Day | Count of order-grain rows | None | Excludes `canceled` and `unavailable`; purchase date is the time grain. |
| `customers` | Day | Distinct `customer_unique_id` | None | Uses person-level identifier, not order-level `customer_id`. |
| `average_order_value` | Day | Merchandise value | Included orders | Freight and payment reconciliation differences are excluded from the numerator. |
| `repeat_customer_rate` | Day | Distinct customers whose commercial order number is greater than one | Distinct included customers that day | Order sequence is evaluated over the person's full observed history. |
| `on_time_delivery_rate` | Day | Delivered orders with `delivered_at <= estimated_delivery_at` | Included orders with both timestamps | Missing delivery promises/outcomes are excluded from the denominator. |
| `average_review_score` | Day | Mean of order-level mean review score | Included reviewed orders | Duplicate review rows are averaged to order grain before the daily mean. |

`canceled` and `unavailable` orders remain in `fct_orders` with
`is_commercial_order = false` so analysts can audit exclusions. Child tables are always aggregated
to order grain before joining: items, payments, and reviews can therefore never multiply one
another in `fct_orders`.
