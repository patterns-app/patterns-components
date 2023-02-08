from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
from .base import get_sql_result, completion
import sqlalchemy
from dataclasses import asdict


sql_requests = Table("sql_requests")
results = Table("data_results", "w")
connection = Parameter("connection", type=Connection("openai"))
api_key = connection.get("api_key")

eng = sqlalchemy.create_engine("postgresql://hmncerbyrjbqdjbitxngwadg%40psql-mock-database-cloud:ptrznvhuauqxboycbnsybukx@psql-mock-database-cloud.postgres.database.azure.com:5432/ecom1675318299004vjaefbbelylvraob")

extract_prompt = """Extract the SQL statement from the following:

{sql}

```
"""

for request in sql_requests.as_stream():
    q = request["question"]
    resp = completion(extract_prompt.format(sql=q), api_key)
    sql = resp.json()["choices"][0]["text"].split("```")[0]
    print(sql)
    qr = get_sql_result(eng, sql)
    request["sql_result"] = asdict(qr)
    results.append(request)
