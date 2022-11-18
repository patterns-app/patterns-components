import json
from datetime import datetime

from patterns_components.components.utilities.generate_date_table.base import generate_date_df


def test_generate_date_table():
    df = generate_date_df(
         start_date=datetime(2000,1,1),
        end_date=datetime(2002, 1, 1),
    )
    assert len(df) == 365 * 2 + 2  # Leap year and inclusive
