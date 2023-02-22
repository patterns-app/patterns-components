select
*
from {{ Table("top_stories") }}
where
    descendants > 3
and to_timestamp(time) < now() - interval '36 month'
and to_timestamp(time) > now() - interval '60 month'