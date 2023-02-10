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


state = State()
data_requests = Table("chart_requests", "r")
sql_results = Table("chart_sql_results", "w")
query_fixes = Table("query_fixes", "w")

connection = Parameter("connection", type=Connection("openai"))
api_key = connection.get("api_key")

schemas = Table("schemas")
schemas = schemas.read()[0]["schemas"]
tables_summary = "\n".join(v for v in json.loads(schemas).values())

eng = sqlalchemy.create_engine("postgresql://hmncerbyrjbqdjbitxngwadg%40psql-mock-database-cloud:ptrznvhuauqxboycbnsybukx@psql-mock-database-cloud.postgres.database.azure.com:5432/ecom1675318299004vjaefbbelylvraob")


def sql_chart_completion(question, n):
    question = question.strip()
    

    prompt = f"""{tables_summary}


As a senior analyst, given the above schemas and data, write a detailed and correct Postgres sql query to produce data for the following requested chart:

"{question}"

Comment the query with your logic."""

    resp = completion(prompt, api_key, n=n)
    return resp


def handle_question(request: dict) -> dict:
    q = request["question"]
    resp = sql_chart_completion(q, 5)
    queries = []
    qr = sql_completion_pipeline(eng, resp.json()["choices"], api_key, tables_summary, query_fixes)
    request["sql_result"] = asdict(qr)
    sql_results.append(request)


#handle_question({"question": "show me a chart of monthly new customers"})


for request in data_requests.as_stream():
    handle_question(request)    
    


