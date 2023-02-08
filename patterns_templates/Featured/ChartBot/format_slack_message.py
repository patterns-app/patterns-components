from patterns import (
    Parameter,
    State,
    Table,
)
from slack_sdk import WebClient
from slack_sdk.models.blocks import HeaderBlock, ImageBlock, SectionBlock
from .base import format_result_as_table

chart_results = Table("chart_results", "r")
data_results = Table("data_results", "r")

state = State()
#state.set_value("latest_streamed_lrkkaxq3_patterns_id", "01grqcqr43cbjr4vjxtabrm0cr")

from patterns import Connection, Parameter, Table

auth = Parameter("slack", type=Connection("slackbot"))

chart_results = Table("chart_results", "r")


slack = WebClient(token=auth["token"])

def format_sql(sql):
    return f"""Here's the SQL I used to generate the data:
```
{sql.strip()}
```
"""

def format_python(py):
    return f"""Here's the Python I used to generate the chart:
```
{py.strip()}
```
"""


for result in chart_results.as_stream():
    channel = result["slack_channel"]
    blocks = [
        SectionBlock(text="Here's what I got"),
        ]
    if result["plot_result"]:
        if result["plot_result"]["error"]:
            blocks.append(SectionBlock(text=result["plot_result"]["error"]))
        else:
            blocks.append(
                ImageBlock(image_url=result["plot_result"]["chart_url"], alt_text="Test")
            )
    if result["sql_result"]["error"]:
        blocks.append(SectionBlock(text=result["sql_result"]["error"]))
    blocks.append(SectionBlock(text=format_sql(result["sql_result"]["sql"])))
    if result["sql_result"]["result"]:
        blocks.append(SectionBlock(text=format_result_as_table(result["sql_result"]["result"])))
    if result["plot_result"]:
        blocks.append(SectionBlock(text=format_python(result["plot_result"]["python"])))
    response = slack.chat_postMessage(
        channel=channel or "C03J9KE9KE0",
        blocks=blocks,
        text=f"Here's what I got",
    )
    print(response)


for result in data_results.as_stream():
    channel = result["slack_channel"]
    blocks = [
        SectionBlock(text="Here's what I got"),
        ]
    if result["sql_result"]["error"]:
        blocks.append(SectionBlock(text=result["sql_result"]["error"]))
    blocks.append(SectionBlock(text=format_sql(result["sql_result"]["sql"])))
    if result["sql_result"]["result"]:
        blocks.append(SectionBlock(text=format_result_as_table(result["sql_result"]["result"])))
    response = slack.chat_postMessage(
        channel=channel or "C03J9KE9KE0",
        blocks=blocks,
        text=f"Here's what I got",
    )
    print(response)