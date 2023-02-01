# Classify Product Reviews

This app classifies negative customer reviews of Asana to determine what the core issues are with the product

## How It Works

It uses cohere's co.classify API to take in a small amount of training data and apply it to their large language model to interpret thousands of customer reviews.


## Getting Started


## 1. Clone the Google Sheet

Clone this sheet and update the google sheets components to have your sheet's id.

https://docs.google.com/spreadsheets/d/17hiRasG2woL2QaFGtpN43x1MlcMFWLQn0vlTLa2s6bU/edit#gid=1415998406

## 2. Create a Google Sheets Connection

Click on the connections tab and create a google sheets connection with the account that you cloned the sheet with.
Then update the Google sheets nodes to use your newly created connection by clicking on each node and selecting your connecton in the settings tab.

## 3. Create a Cohere Connection

Go to cohere.ai and create an account. Then, on your dashboard there will be a cohere test API key. Copy it.

Then go back to connections and create a cohere connection using the testing API key you copied.