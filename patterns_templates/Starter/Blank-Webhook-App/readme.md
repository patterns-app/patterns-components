# Blank Webhook App

A starter app for ingesting data via webhook and processing streaming data in Patterns.

To get started, first copy the webhook url from the webhook node details tab and hook it up to
an event stream of interest (or use Postman/curl to test with). Webhooks accept a single
JSON record or an array of JSON records as payload. As events come in they are 
streamed to the webhook Table, where they can be processed in a streaming or aggregate manner by 
the downstream python node.

Check out [intro to streaming and webhooks](https://www.patterns.app/docs/dev/streams) or the
[python reference](https://www.patterns.app/docs/reference/python-reference) in the docs
for more details on working with webhooks and streaming data in Patterns.
