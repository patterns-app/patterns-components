# Documentation: https://docs.patterns.app/docs/node-development/python/

from patterns import (
    Parameter,
    State,
    Stream,
    Table,
)

# define table input / output
horizon_returns = Table("horizon_returns")
alert_stream = Table("alert_stream", mode="w")
alert_stream.init(strictly_monotonic_ordering='timestamp')

# set your alert threashold parameters here
# currently configured to detect stocks that have lost more than 5% in 2 weeks
sql = "select * from {{ horizon_returns }} where week_ago = 2 and percent_return > -5"
returns = horizon_returns.read_sql(sql)

# iterate and send an alert to slack
for row in returns:
    alert_stream.append(row)
