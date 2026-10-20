with assignments as (
    select * from {{ ref('fct_experiment_assignments') }}
), totals as (
    select count(*) as total_assignments from assignments
), group_counts as (
    select segment, count(*) as observed_count
    from assignments
    group by segment
), duplicate_count as (
    select count(*) as duplicate_source_row_key_count
    from (
        select experiment_customer_id
        from assignments
        group by experiment_customer_id
        having count(*) > 1
    ) duplicates
)

select
    group_counts.segment,
    group_counts.observed_count,
    cast(group_counts.observed_count as double precision)
        / nullif(totals.total_assignments, 0) as observed_share,
    duplicate_count.duplicate_source_row_key_count
from group_counts
cross join totals
cross join duplicate_count
