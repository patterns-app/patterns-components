## Step 3: Generate embeddings for previous Discord messages

Set the *discord_server_id* parameter for this node. 
The discord server id is the id of the server you added your bot to. 
You can get it from the url when you're on your server 
(it's the long number after /channels/ but not the very last number) 
For example, https://discord.com/channels/1062086264112816179/1063240344843604078 -> 
server id is 1062086264112816179

Run this node which will also run the downstream nodes
- :Node{#yrvu6my5} - outputs all of your server's channels to a table
- :Node{#k5vx4axz} - outputs all messages within each channel to a table
- :Node{#udtlojl6} - outputs the embedding for each message to a table

__Step 4. Generate embeddings for documentation website - :Node{#akl3gegx}__
