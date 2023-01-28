select
    prediction,
    count(prediction)
from {{ Table("cohere_output") }}
where
    "Score" > 20 and
    confidence > 0.8
group by prediction