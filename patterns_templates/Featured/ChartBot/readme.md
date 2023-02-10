# ChartBot

A slack bot that uses GTP-3 to generate SQL and matplotlib charts from free-form analytics texts.

The ChartBot app takes in a free-form analytics query via Slack (e.g "How many seed rounds happened in 
2022?") and uses GPT-3 to generate SQL and or charts and return the answer via Slack. See blog post 
for details: https://www.patterns.app/blog/2023/02/07/chartbot-sql-analyst-gpt

You'll need an OpenAI API key, a Slack bot token authed against your organization, and an S3 bucket.
