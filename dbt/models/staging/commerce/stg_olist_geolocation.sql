select
    cast(geolocation_zip_code_prefix as varchar) as geolocation_zip_code_prefix,
    cast(nullif(cast(geolocation_lat as varchar), '') as double precision) as latitude,
    cast(nullif(cast(geolocation_lng as varchar), '') as double precision) as longitude,
    lower(trim(cast(geolocation_city as varchar))) as city,
    upper(trim(cast(geolocation_state as varchar))) as state,
    cast(_loaded_at as timestamp) as loaded_at
from {{ source('raw', 'geolocation') }}
