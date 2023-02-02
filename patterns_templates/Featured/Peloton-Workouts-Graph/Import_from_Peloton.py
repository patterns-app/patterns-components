from patterns import (
    Parameter,
    Table,
)

import requests
import pandas as pd
import io

workouts = Table("table2", mode="w")

pton_password = Parameter("pton_password", type=str, default=None)
pton_username = Parameter("pton_username", type=str, default=None)

s = requests.Session()
payload = {'username_or_email': pton_username, 'password': pton_password}
s.post('https://api.onepeloton.com/auth/login', json=payload)

url = "https://api.onepeloton.com/api/user/ba2ede88792b4d0496fce774b610c7be/workout_history_csv"

resp=s.get(url).content
c=pd.read_csv(io.StringIO(resp.decode('utf-8')))

print(c)

workouts.write(c, replace = True)
