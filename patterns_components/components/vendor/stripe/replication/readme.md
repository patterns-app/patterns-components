# Stripe Replication

Replicate essential Stripe tables from the REST API. By default, it refreshes records up to 90 days old to
check for updates, configurable with the `curing_window_days` parameter.

Required parameters:
* `api_key`: obtain from the Stripe [API keys](https://dashboard.stripe.com/apikeys) page. Must 
  be a *secret* key, not a *publishable* key.

Optional parameters:
* `curing_window_days`: how many days back to look for updated records
