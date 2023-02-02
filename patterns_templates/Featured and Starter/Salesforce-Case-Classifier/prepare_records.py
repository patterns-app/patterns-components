from patterns import (
    Parameter,
    State,
    Table,
)

from pandas import DataFrame, concat
import json

webhook_results = Table("webhook_results", "r")
sf_testing = Table("sf_testing", "w")

stream_results = webhook_results.as_stream(order_by="timestamp")

records = []

for result in stream_results.consume_records():
    data = result['record']
    record = json.loads(data) if type(data) == 'string' else data
    print(data)
    records.append(record)

df = DataFrame(records, columns=['Id', 'Subject'])
sf_testing.write(df)