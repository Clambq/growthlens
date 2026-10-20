select
    customers.channel,
    customers.zip_code,
    assignments.segment,
    count(*) as customers,
    avg(cast(outcomes.converted as double precision)) as conversion_rate,
    avg(cast(outcomes.spend as double precision)) as average_spend,
    'exploratory_not_confirmatory' as interpretation_label
from {{ ref('dim_experiment_customers') }} customers
inner join {{ ref('fct_experiment_assignments') }} assignments
    on customers.experiment_customer_id = assignments.experiment_customer_id
inner join {{ ref('fct_experiment_outcomes') }} outcomes
    on customers.experiment_customer_id = outcomes.experiment_customer_id
group by customers.channel, customers.zip_code, assignments.segment
