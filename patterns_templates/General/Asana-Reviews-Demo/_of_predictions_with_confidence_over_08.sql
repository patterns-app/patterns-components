with stg as (
    select count(1) as total from {{ Table("cohere_output") }}
),
stg2 as (
    select count(1) as count from {{ Table("cohere_output") }}
    where "confidence" > 0.8
),
stg3 as (
    select
        round((cast(stg2.count as float) / stg.total * 100) - 1) as percent_above_threshold
    from stg
    full outer join stg2 on 1 = 1
)

select
    format('%s%%', percent_above_threshold) as out_str
from stg3