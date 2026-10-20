select
    cast(_row_hash as varchar) as experiment_row_id,
    cast(recency as integer) as recency_months,
    cast(history_segment as varchar) as history_segment,
    cast(history as decimal(18, 2)) as history_value,
    cast(mens as integer) = 1 as purchased_mens,
    cast(womens as integer) = 1 as purchased_womens,
    cast(zip_code as varchar) as zip_code,
    cast(newbie as integer) = 1 as is_new_customer,
    cast(channel as varchar) as channel,
    cast(segment as varchar) as segment,
    cast(visit as integer) as visited,
    cast("conversion" as integer) as converted,
    cast(spend as decimal(18, 2)) as spend,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'hillstrom') }}
