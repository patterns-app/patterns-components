-- Type '{{' to use Tables and Parameters
Select date_trunc('year', "Workout Timestamp"::DATE) as year
, count(distinct "Workout Timestamp") as count_workouts

From {{ Table("table2") }}

GROUP BY date_trunc('year', "Workout Timestamp"::DATE)
