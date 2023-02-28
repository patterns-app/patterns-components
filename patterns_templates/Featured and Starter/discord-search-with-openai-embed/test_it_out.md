## Step 6: Test is out!

All 3 embedding inputs tables to node :Node{#d3kirmsk} should be filled in, and 
the webhook is configured with the created slash command. To test it, 
go to the connected discord server and enter "/search" followed by the text you 
want to search for. Upon submitting, the Patterns webhook will run and should 
update the discord message with the top 5 results matching your search. 

- :Node{#k5bi6l7z} - outputs the search text from the incoming webhook to a table
- :Node{#d3kirmsk} - embeds the search text and compares the embedding to 
the previously generated embeddings to find the 5 closest results
- :Node{#arxszeha} - updates the discord message with the top results

