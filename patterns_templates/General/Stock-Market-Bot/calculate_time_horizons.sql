-- Type '{{' to use Tables and Parameters
-- Documentation: https://docs.patterns.app/docs/node-development/sql/

with data as (
    select ticker
            , close
            , timestamp 
            , row_number() over (partition by ticker order by timestamp desc) as week_ago

    from {{ Table("daily_stocks") }}
)

select *
from data 
where week_ago < 12

