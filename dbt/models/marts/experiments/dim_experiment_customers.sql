select
    experiment_row_id as experiment_customer_id,
    recency_months,
    history_segment,
    history_value,
    purchased_mens,
    purchased_womens,
    zip_code,
    is_new_customer,
    channel
from {{ ref('stg_hillstrom_customers') }}
