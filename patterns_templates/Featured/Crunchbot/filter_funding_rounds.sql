-- Type '{{' to use Tables and Parameters

select

uuid
,region
,city
,investment_type
,announced_on
,raised_amount_usd
,post_money_valuation_usd
,investor_count
,org_uuid
,org_name
,lead_investor_uuids

from {{ Table("crunchbase_funding_rounds") }}
