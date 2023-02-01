select * from {{ Table("cohere_output") }}
order by confidence desc