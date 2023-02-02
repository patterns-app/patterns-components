-- Type '{{' to use Tables and Parameters

select
uuid
,name
,roles
,country_code
,region
,city
,status
,short_description
,category_list
,num_funding_rounds
,total_funding_usd
,founded_on
,employee_count
,email
,primary_role
from {{ Table("crunchbase_organizations") }}