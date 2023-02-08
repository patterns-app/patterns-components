import requests
from patterns_components.helpers.api import handle_rate_limiting
from dataclasses import dataclass, asdict, replace
from sqlalchemy import text
import io
import matplotlib.pyplot as plt
import base64
from tabulate import tabulate
import pandas as pd


def table_info(table):
    field_summary = "\n\t".join(
        f.name + " " + f.field_type.name for f in table.schema.fields
    )
    schema_summary = f"""Schema for table: {table.port_name}
    \t{field_summary}
    """

    df = table.read_sql(f"select * from {table} limit 5", as_format="dataframe")

    s = f"""{schema_summary}
Data for table: {table.port_name}:
{df}
    """
    return s


def completion(prompt, api_key, **kwargs):
    params = {
            "prompt": prompt,
            "model": "text-davinci-003",
            "max_tokens": 500,
            "temperature": .8,
        }
    params.update(kwargs)
    # create a completion
    resp = requests.post(
        "https://api.openai.com/v1/completions",
        json=params,
        headers={"Authorization": f"Bearer {api_key}"}
    )
    resp = handle_rate_limiting(resp)
    if not resp.ok:
        print(resp.json())
        resp.raise_for_status()
    return resp


@dataclass(frozen=True)
class QueryResult:
    sql: str
    result: list[dict] = None
    error: str = None


def get_sql_result(eng, sql: str, limit=50) -> QueryResult:
    print(sql)
    error = None
    result = []
    try:
        curs = eng.connect().execute(text(sql))
        for r in curs:
            result.append({k: v for k, v in zip(curs.keys(), r)})
            if len(result) >= limit:
                break     
        print(result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)
        try:
            error = str(e.__dict__['orig'])
        except KeyError:
            error = str(e)
    return QueryResult(sql=sql, result=result, error=error)



def double_check_query(sql: str, api_key: str, tables_summary: str) -> str:

    prompt = f"""
{tables_summary}



{sql}


Double check the Postgres query above for common mistakes, including:
 - Remembering to add `NULLS LAST` to an ORDER BY DESC clause
 - Handling case sensitivity, e.g. using ILIKE instead of LIKE
 - Ensuring the join columns are correct
 - Casting values to the appropriate type
 - Properly quoting identifiers when required (e.g. table."Sales Amount")
 
 Rewrite the query below if there are any mistakes. If it looks good as it is, just reproduce the original query."""

    resp = completion(prompt, api_key)
    corrected_sql = resp.json()["choices"][0]["text"]
    return {"original": sql, "corrected": corrected_sql}


def fix_sql_bug(query: QueryResult, api_key, tables_summary: str) -> QueryResult:

    error_prompt = f"""
{tables_summary}



{query.sql}


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
    resp = completion(prompt, api_key)
    corrected_sql = resp.json()["choices"][0]["text"]
    return {"original": query.sql, "corrected": corrected_sql}


def sql_completion_pipeline(eng, completions: list, api_key: str, tables_summary: str, query_fixes) -> QueryResult:
    for completion in completions:
        sql = completion["text"]
        corrected = double_check_query(sql, api_key, tables_summary)
        print(corrected)
        corrected["type"] = "sql-double-check"
        query_fixes.append(corrected)
        qr = get_sql_result(eng, corrected["corrected"])
        if qr.error or not qr.result:
            # Try to fix error (just once for now)
            corrected = fix_sql_bug(qr, api_key, tables_summary)
            print(corrected)
            corrected["type"] = "sql-error"
            query_fixes.append(corrected)
            qr = get_sql_result(eng, corrected["corrected"])
        if qr.result:
            break
    else:
        if qr.error:
            qr = replace(qr, result = f"Stumped me. Here's the SQL I came up with but it had the following error: {qr.error}.")
        else:
            qr = replace(qr, result=f"Stumped me. Here's the SQL I came up with but it didn't return a result.")
    return qr


def format_result_as_table(res):
    if res and isinstance(res, list):
        return tabulate(res, headers="keys")
    return res


@dataclass(frozen=True)
class PlotResult:
    python: str
    result: str = None
    error: str = None


def get_plot_result(py: str, data):
    print(py)
    error = None
    buf = io.BytesIO()
    result = None
    def get_data():
        return pd.DataFrame.from_records(data)
    try:
        exec(py, {"get_data": get_data})
        
        plt.savefig(buf, format='png')
        buf.seek(0)
    except Exception as e:
        import traceback
        error = traceback.format_exc()
        print(error)
    #if buf:
    #    result = base64.b64encode(buf.getvalue()).decode("utf-8").replace("\n", "")
    return PlotResult(python=py, result=buf, error=error)


def fix_python_bug(result: PlotResult, api_key) -> PlotResult:

    prompt = f"""
```
{result.python}
```


```
{result.error}
```

Above is the code and the error it produced. Here is the corrected code:

```
"""

    print("ERROR")
    resp = completion(prompt, api_key)
    corrected = resp.json()["choices"][0]["text"]
    corrected = corrected.split("```")[0]
    return {"original": result.python, "corrected": corrected}


pyplot_preamble = """# Import the necessary libraries
import matplotlib.pyplot as plt
import pandas as pd


# Load the data into a pandas dataframe
records_df = get_data()

"""

pyplot_exec_prefix = "plt.style.use(plt.style.library['ggplot'])\n"


def plot_completion_pipeline(completions: list, api_key: str, data: list, query_fixes) -> PlotResult:
    for completion in completions:
        py = completion["text"]
        py = py.split("```")[0]
        py = pyplot_preamble + pyplot_exec_prefix +  py
        pr = get_plot_result(py, data)
        if pr.error or not pr.result:
            # Try to fix error (just once for now)
            corrected = fix_python_bug(pr, api_key)
            print(corrected)
            corrected["type"] = "python-error"
            query_fixes.append(corrected)
            pr = get_plot_result(corrected["corrected"], data)
        if pr.result:
            break
    else:
        if pr.error:
            pr = replace(pr, result = f"Stumped me. Here's the SQL I came up with but it had the following error: {qr.error}.")
        else:
            pr = replace(pr, result=f"Stumped me. Here's the SQL I came up with but it didn't return a result.")
    return pr
