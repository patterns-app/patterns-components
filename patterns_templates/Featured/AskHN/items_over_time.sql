select
date_trunc('month', to_timestamp(time)) as month
, count(*)
from {{ Table("top_stories") }}
group by 1 order by 1