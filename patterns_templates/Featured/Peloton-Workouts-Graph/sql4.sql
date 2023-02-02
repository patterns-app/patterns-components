-- Type '{{' to use Tables and Parameters

select sum("Distance (mi)") as total_distance_miles from {{ Table("table2") }}