Select date_trunc('year', "Workout Timestamp"::DATE) as year
, count(distinct "Workout Timestamp") as count_workouts
, ceil(sum("Distance (mi)")) as total_distance_per_year
, ceil(sum("Total Output")) as total_output_per_year
, ceil(sum("Length (minutes)")) as total_minutes_per_year
, sum("Total Output") / sum("Length (minutes)") as avg_output_per_year

From {{ Table("table2") }}

WHERE "Total Output" > 100

GROUP BY date_trunc('year', "Workout Timestamp"::DATE)