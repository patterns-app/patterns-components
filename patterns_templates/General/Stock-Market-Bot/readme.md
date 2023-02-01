# Stock Market Bot

Build a bot that charts stock market data and sends alerts to Slack alerts when conditions are met.

1. Import data from Alphavantage API
2. Compute stock returns over time horizons (1-12 weeks)
3. Chart time series data 
4. Send alerts to Slack when certain conditions are met

### Configuration
1. Go to [Alphavantage](https://www.alphavantage.co/support/#api-key) and get a free API key
2. Create a secret named `alphavantage_api_key` by either clicking on `Import Stock Data` node and adding it there. Or adding it in the sidebar. 
3. Follow instructions on the Slack component to configure a Slack App