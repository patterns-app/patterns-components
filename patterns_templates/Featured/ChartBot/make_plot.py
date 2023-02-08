from patterns import (
    Parameter,
    State,
    Table,
    Connection
)
from collections import Counter
from dataclasses import dataclass, asdict, replace
import requests
from patterns_components.helpers.api import handle_rate_limiting
from .base import table_info, completion, double_check_query, fix_sql_bug, get_sql_result, sql_completion_pipeline, plot_completion_pipeline, pyplot_preamble
import sqlalchemy
import json
import base64
from slack_sdk import WebClient
import boto3
import time


state = State()

#state.set_value("latest_streamed_u4uzx3lq_patterns_id", "01grq2kch3w1md4n4wx9fb3kf5")


sql_results = Table("chart_sql_results")
chart_results = Table("chart_results", "w")
query_fixes = Table("query_fixes", "w")
#chart_results.init(schema_hints={"result": "Text"})

connection = Parameter("connection", type=Connection("openai"))
api_key = connection.get("api_key")


aws_secret = Parameter("aws_secret")

schemas = Table("schemas")
schemas = schemas.read()[0]["schemas"]
tables_summary = "\n".join(v for v in json.loads(schemas).values())

eng = sqlalchemy.create_engine("postgresql://hmncerbyrjbqdjbitxngwadg%40psql-mock-database-cloud:ptrznvhuauqxboycbnsybukx@psql-mock-database-cloud.postgres.database.azure.com:5432/ecom1675318299004vjaefbbelylvraob")



def chart_completion(question, n, result):
    question = question.strip()
    
    result = result[:50]
    prompt = f"""records_df = pd.DataFrame.from_records({result})


As a senior analyst, given the above data set, write detailed and correct matplotlib code to produce a chart as requested:

"{question}"

Comment the code with your logic. Use plt.show() to display the plot at the end.

```
""" + pyplot_preamble
    print(prompt)
    resp = completion(prompt, api_key, n=n)
    return resp


def upload_image_s3(buf):
    client = boto3.client('s3', region_name='us-west-2', aws_access_key_id="AKIA4YJBXR25XPDISZEV", aws_secret_access_key=aws_secret)
    fname = f'chart-{int(time.time())}.png'
    resp = client.upload_fileobj(buf, 'patterns-files', fname)
    return "https://patterns-files.s3.us-west-2.amazonaws.com/" + fname


def handle_question(request: dict) -> dict:
    result = request["sql_result"]
    if result["error"]:
        request["plot_result"] = {}
        return request
    resp = chart_completion(request["question"], 3, result["result"])
    pr = plot_completion_pipeline(resp.json()["choices"], api_key, result["result"], query_fixes)
    resp = None
    if pr.result:
        url = upload_image_s3(pr.result)
    request["plot_result"] = {"python": pr.python, "chart_url": url, "error": pr.error}
    return request


for request in sql_results.as_stream():
    result = handle_question(request)    
    chart_results.append(result)

