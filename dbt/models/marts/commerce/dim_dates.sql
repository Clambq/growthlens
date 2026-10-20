select distinct
    cast(purchased_at as date) as date_day,
    extract(year from purchased_at) as year_number,
    extract(month from purchased_at) as month_number,
    extract(day from purchased_at) as day_number,
    extract(dow from purchased_at) as weekday_number
from {{ ref('stg_olist_orders') }}
where purchased_at is not null
