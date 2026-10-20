select
    experiment_row_id as experiment_customer_id,
    visited,
    converted,
    spend
from {{ ref('stg_hillstrom_customers') }}
