select
    prediction,
    count(prediction)
from {{ Table("cohere_output") }}
where
    confidence > 0.8
group by prediction