select
    date_trunc('month', received_at) as month
  , count(*) as lead_count
  , count(case when score > 15 then 1 end) as high_priority_lead_count
from {{  Table("scored_leads") }}
group by 1
order by 1