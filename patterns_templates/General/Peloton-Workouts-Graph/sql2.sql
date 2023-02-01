-- Type '{{' to use Tables and Parameters

select "Instructor Name", sum("Total Output") as "sum_output" from {{  Table("table2") }} group by "Instructor Name"
