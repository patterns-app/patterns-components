-- Type '{{' to use Tables and Parameters

select "Total Output"
, "Length (minutes)"
, "Total Output" / "Length (minutes)"::FLOAT  as avg_output
, "Workout Timestamp"
, "Avg. Watts" as "avg_watts"
, "Avg. Resistance" as "avg_resistance"
, "Calories Burned"

from {{ Table("table2") }}

WHERE "Total Output" > 100
