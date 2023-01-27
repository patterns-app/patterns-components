import re

from patterns import (
    Parameter,
    State,
    Table,
)
import pandas as pd

pd.set_option("display.max_columns", None)


table = Table("prompts", "w")
questions = Table("questions")
orgs = Table("organizations")
investments = Table("investments")
funding_rounds = Table("funding_rounds")

analytical_tables = [orgs, investments, funding_rounds]



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


def build_prompt(question):
    question = question.strip()
    tables_summary = "\n\n".join(table_info(t) for t in analytical_tables)

    prompt = f"""{tables_summary}


As a senior analyst, given the above schemas and data, write a detailed and correct Postgres sql query to answer the analytical question:

"{question}"

Comment the query with your logic."""

    print(prompt)
    return prompt


# prompt = build_prompt(question)
# table.append({"prompt": prompt, "question": question, "slack_channel": "kvh-test"})


for question in questions.as_stream():
    prompt = build_prompt(question["question"])
    question["prompt"] = prompt
    table.append(question)
