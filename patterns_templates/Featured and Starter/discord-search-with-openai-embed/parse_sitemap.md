## Step 4: Generate embeddings for documentation website

Set the *sitemap_url* parameter for this node to the url for your 
website's sitemap (such as https://www.patterns.app/sitemap.xml)

Run this node which will also run the downstream nodes
- :Node{#akl3gegx} - parses the sitemap.xml file and outputs all of the webpage urls to a table
- :Node{#ui2vd6i4} - scrapes the content from each of the webpages, and outputs it to a table 
- :Node{#qgmaykcl} - outputs the embedding for each webpage to a table


__Step 5. Generate embeddings for github repo open issues - :Node{#5gm67t4w}__
