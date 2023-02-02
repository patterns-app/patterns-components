from patterns import (Parameter, State, Stream, Table)
import requests
import pandas as pd
import io

api_key = Parameter("alphavantage_api_key", type=str)
daily_stocks = Table("daily_stocks", "w")

tickers = ['TWTR', 'SQ', 'TWLO', 'META']

all_data = pd.DataFrame(columns=['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])

for ticker in tickers:
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={ticker}&apikey={api_key}&datatype=csv&outputsize=compact'
    r = requests.get(url).content
    ticker_data = pd.DataFrame(columns=['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    ticker_data = pd.read_csv(io.StringIO(r.decode('utf-8')))
    ticker_data['ticker'] = ticker
    all_data = pd.concat([all_data, ticker_data], axis=0)
    print(f'completed processing {ticker}')

daily_stocks.write(all_data, replace=True)