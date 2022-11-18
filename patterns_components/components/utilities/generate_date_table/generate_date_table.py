from datetime import datetime, timedelta

from patterns import Parameter, Table

from .base import generate_date_df


dates_table = Table("dates", "w", schema="DateTable")
start_date = Parameter("start_date", type=datetime, default="2000-01-01")
end_date = Parameter("end_date", type=datetime, default="2030-01-01")

print(start_date)
print(end_date)

dates = generate_date_df(start_date, end_date)

print(dates.head())

dates_table.replace(dates)
