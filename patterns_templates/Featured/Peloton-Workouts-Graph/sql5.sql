-- Type '{{' to use Tables and Parameters

select "Instructor Name", sum("Distance (mi)") as "total_distance" from {{  Table("table2") }} group by "Instructor Name"

