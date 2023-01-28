from patterns import (
    Parameter,
    State,
    Table,
    Connection
)
from collections import Counter
from dataclasses import dataclass, asdict
import requests
from patterns_components.helpers.api import handle_rate_limiting
from sqlalchemy import text


completions = Table("completions", "r")
results = Table("results", "w")
sql_fixes = Table("sql_fixes", "w")

results.init(schema_hints={"result": "Text"})

orgs = Table("organizations")
investments = Table("investments")
funding_rounds = Table("funding_rounds")

connection = Parameter("connection", type=Connection("openai"))

analytical_tables = [orgs, investments, funding_rounds]

api_key = connection.get("api_key")

state = State()




@dataclass
class Query:
    sql: str
    result: list[dict] = None
    error: str = None


def inject_tables(s):
    for t in analytical_tables:
        s = s.replace(t.port_name, str(t))
    return s


def get_sql_result(q, limit=50):
    try:
        sql = inject_tables(q.sql)
        print(sql)
        result = None
        #for r in orgs.read_sql(sql, chunksize=200):
        result = []
        curs = orgs._get_db_api().get_engine().connect().execute(text(sql))
        for r in curs:
            result.append({k: v for k, v in zip(curs.keys(), r)})
            if len(result) >= limit:
                break
            
        q.result = result
        print(result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)
        try:
            error = str(e.__dict__['orig'])
        except KeyError:
            error = str(e)
        q.error = error


def double_check_query(query: Query):

    prompt = f"""{query.sql}


Double check the Postgres query above for common mistakes, including:
 - Remembering to add `NULLS LAST` to an ORDER BY DESC clause
 - Handling case sensitivity, e.g. using ILIKE instead of LIKE
 - Ensuring the join columns are correct
 - Casting values to the appropriate type
 - Properly quoting identifiers
 
 Rewrite the query below if there are any mistakes. If it looks good as it is, just reproduce the original query."""

    # create a completion
    resp = requests.post(
        "https://api.openai.com/v1/completions",
        json={
            "prompt": prompt,
            "model": "text-davinci-003",
            "max_tokens": 500,
            "temperature": .8,
        },
        headers={"Authorization": f"Bearer {api_key}"}
    )
    resp = handle_rate_limiting(resp)
    if not resp.ok:
        print(resp.json())
        resp.raise_for_status()

    q = Query(sql=resp.json()["choices"][0]["text"])
    if q.sql == query.sql:
        return query
    sql_fixes.append({"original": asdict(query), "fixed": asdict(q), "type": "double-check"})
    return q


def fix_bug(query: Query):

    error_prompt = f"""{query.sql}


The query above produced the following error:

{query.error}


Rewrite the query with the error fixed:"""

    no_result_prompt = f"""{query.sql}


The query above produced no result. Try rewriting the query so it will return results:"""

    print("ERROR")
    if query.error:
        prompt = error_prompt
    else:
        prompt = no_result_prompt
    print(prompt)
    # create a completion
    resp = requests.post(
        "https://api.openai.com/v1/completions",
        json={
            "prompt": prompt,
            "model": "text-davinci-003",
            "max_tokens": 500,
            "temperature": .8,
        },
        headers={"Authorization": f"Bearer {api_key}"}
    )
    resp = handle_rate_limiting(resp)
    if not resp.ok:
        print(resp.json())
        resp.raise_for_status()

    q = Query(sql=resp.json()["choices"][0]["text"])

    sql_fixes.append({"original": asdict(query), "fixed": asdict(q), "type": "error"})
    get_sql_result(q)
    return q

def pick_best_query(queries):
    for q in queries:
        for q2 in queries:
            if q.result and q.result == q2.result:
                # First dupe match
                return q
    for q in queries:
        if q.result:
            return q
    return queries[0]


queries = []

for record in completions.as_stream():
    for completion in record["completion"]:
        q = Query(sql=completion["text"])
        q = double_check_query(q)
        get_sql_result(q)
        if q.error or not q.result:
            # Try to fix error
            q = fix_bug(q)
        queries.append(q)
    q = pick_best_query(queries)
    if not q.result:
        if q.error:
            q.result = f"Stumped me. Here's the SQL I came up with but it had the following error: {q.error}."
        else:
            q.result = f"Stumped me. Here's the SQL I came up with but it didn't return a result."
    record["result"] = asdict(q)
    results.append(record)
