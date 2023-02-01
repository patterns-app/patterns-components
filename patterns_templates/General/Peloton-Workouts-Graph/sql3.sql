-- Type '{{' to use Tables and Parameters

select "Total Output"
, "Length (minutes)"
, "Total Output" / "Length (minutes)"::FLOAT  as avg_output
, "Workout Timestamp"

from {{ Table("table2") }}

WHERE "Total Output" > 100
