## Step 1: Create Discord Bot and setup Discord webhook

- Create new discord application using their developer portal
https://discord.com/developers/applications

- Click *New Application* and enter a name for your application 
(such as "Patterns Semantic Search")

- Once application is created, on the *Bot* tab, click *Add Bot*

- Give your bot *MESSAGE CONTENT INTENT* permissions by turning the toggle 
on under the *Privileged Gateway Intents* section

- Enter this url into your web browser and add bot to discord server of your choosing
	https://discord.com/api/oauth2/authorize?client_id={{Bot_Application_ID}}&permissions=2147552256&scope=bot
	- the bot application ID is located on the *General Information* page for the bot
	- If you're curious, this url gives the bot the following permissions:
		 - Read Messages/View Channels
		 - Send Messages
		 - Read Message History
		 - Use Slash Commands 

- Copy the application's *Public Key* located under the *General Information* page. 
(We'll use it to configure the webhook node within your Pattern's app next.)

- On your Patterns app's page, create a secret for your Discord Application's public
key. (Call the secret "APPLICATION_PUBLIC_KEY"). Paste in the key you copied 
from discord and hit update.

- Under the *Settings* tab for this node, configure the "APPLICATION_PUBLIC_KEY" 
parameter to use the newly created *APPLICATION_PUBLIC_KEY* secret

- At the top of this node's *Readme* tab, copy the node's webhook url. 
	
- Go back to your discord bot. Under the *General Information* tab, 
	paste the copied url into the "INTERACTIONS ENDPOINT URL" field, and hit save. 
	Confirm that the change is saved. If it's not, then something is wrong with your 
	configuration up to this point.


__Step 2. Configure Discord webhook with our custom search command - :Node{#rxxxe6ou}__



