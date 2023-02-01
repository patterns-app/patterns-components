-- Type '{{' to use Tables and Parameters

select
uuid
, name
, funding_round_uuid
, funding_round_name
, investor_uuid
, investor_name
, investor_type
, is_lead_investor
from {{ Table("crunchbase_investments") }}