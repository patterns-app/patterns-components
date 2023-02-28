## Step 2: Configure Discord webhook with our custom search command

- On the Discord application's page, under the *Bot* tab, click the "Reset Token" button and 
copy the new token value. 

- On your Patterns app's page, create a secret for your Bot's token 
(secret's name is "discord_bot_token"). Paste in the token you copied 
from discord. 

- Under the Settings tab for this node, configure the "discord_bot_token" 
parameter to use the newly created *discord_bot_token* secret

- Get the application id for the Discord app (on the *General Information* tab), copy it, 
and enter it as the value for the *application_id* parameter for this node 


- Run this node to register a new slash command with the new bot. 
(This node needs to be successfully run before the app's slash command will work)

__Step 3. Generate embeddings for previous Discord messages - :Node{#yrvu6my5}__
