from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
from .base import completion



questions = Table("questions", "r")
sql_requests = Table("sql_requests", "w")
chart_requests = Table("chart_requests", "w")
data_requests = Table("data_requests", "w")

connection = Parameter("connection", type=Connection("openai"))
api_key = connection.get("api_key")


prompt = """Classify the following message according to whether it is a SQL query, a data request, or a chart request. Examples:

message: how many new customers were added last year?
class: data request

message: show me the trend in house prices over the last 5 years
class: chart request

message: plot a graph of miles vs heartrate, grouped by age group
class: chart request

message: SELECT * FROM customers ORDER BY date
class: sql query

message: {question}
class: 
"""


for question in questions.as_stream():
    prompt = prompt.format(question=question["question"])
    resp = completion(prompt, api_key)
    question["route"] = resp.json()["choices"][0]["text"]
    print(question)
    if "sql" in question["route"].lower():
        sql_requests.append(question)
    elif "chart" in question["route"].lower():
        chart_requests.append(question)
    elif "data" in question["route"].lower():
        data_requests.append(question)
    else:
        print(f"Unknown route!")
        data_requests.append(question)
    
