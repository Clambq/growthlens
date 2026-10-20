select
    assignments.segment,
    count(*) as customers,
    avg(cast(outcomes.visited as double precision)) as visit_rate,
    avg(cast(outcomes.converted as double precision)) as conversion_rate,
    avg(cast(outcomes.spend as double precision)) as average_spend,
    sum(cast(outcomes.spend as double precision)) as total_spend
from {{ ref('fct_experiment_assignments') }} assignments
inner join {{ ref('fct_experiment_outcomes') }} outcomes
    on assignments.experiment_customer_id = outcomes.experiment_customer_id
group by assignments.segment
