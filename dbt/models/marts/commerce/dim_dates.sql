with bounds as (
    select
        min(cast(purchased_at as date)) as min_date,
        max(cast(purchased_at as date)) as max_date
    from {{ ref('stg_olist_orders') }}
    where purchased_at is not null
), dates as (
    select cast(series.date_day as date) as date_day
    from bounds
    cross join generate_series(
        bounds.min_date,
        bounds.max_date,
        interval '1 day'
    ) as series(date_day)
)

select
    date_day,
    extract(year from date_day) as year_number,
    extract(month from date_day) as month_number,
    extract(day from date_day) as day_number,
    extract(dow from date_day) as weekday_number
from dates
