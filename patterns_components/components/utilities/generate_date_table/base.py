from datetime import datetime

import pandas as pd
from pandas.tseries.offsets import Day, BDay


def generate_date_df(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    bday = BDay()
    dates = pd.DataFrame(index=pd.date_range(start=start_date, end=end_date, freq="D"))
    dates.index.name = "date"
    dates["year"] = dates.index.year
    dates["month"] = dates.index.month
    dates["day"] = dates.index.day
    dates["day_of_week"] = dates.index.dayofweek
    dates["day_of_week_name"] = dates.index.day_name()
    dates["week"] = dates.index.isocalendar().week
    dates["quarter"] = dates.index.quarter
    dates["year_half"] = dates.index.month.map(lambda mth: 1 if mth < 7 else 2)
    dates["is_business_day"] = dates.index.map(lambda dt: bday.is_on_offset(dt))
    dates["is_month_start"] = dates.index.is_month_start
    dates["is_month_end"] = dates.index.is_month_end
    dates["is_quarter_start"] = dates.index.is_quarter_start
    dates["is_quarter_end"] = dates.index.is_quarter_end
    dates["is_year_start"] = dates.index.is_year_start
    dates["is_year_end"] = dates.index.is_year_end
    dates["is_leap_year"] = dates.index.is_leap_year

    dates.reset_index(inplace=True)
    return dates

