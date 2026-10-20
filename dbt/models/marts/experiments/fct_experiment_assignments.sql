select
    experiment_row_id as experiment_customer_id,
    segment
from {{ ref('stg_hillstrom_customers') }}
