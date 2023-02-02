-- Type '{{' to use Tables and Parameters
-- Documentation: https://docs.patterns.app/docs/node-development/sql/

with recent as (
    select *
    from {{ Table("price_horizons") }}
    where week_ago = 1
)

select ph.ticker
        , ph.week_ago
        , ph.timestamp
        , trunc(((r.close - ph.close)/ph.close*100)::numeric, 2) as percent_return

from {{ Table("price_horizons") }} as ph
left join recent as r 
on r.ticker = ph.ticker
where ph.week_ago != 1
order by week_ago desc