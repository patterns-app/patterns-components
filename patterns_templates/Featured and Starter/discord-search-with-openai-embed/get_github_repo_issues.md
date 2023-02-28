## Step 5: Generate embeddings for github repo open issues

Create a fine-grained personal access token here: https://github.com/settings/tokens?type=beta
Create a new token that has access to the correct github repo, and under repository 
permissions give it "Read-only" permissions to *Issues* and *Metadata*.

Once token is created, copy the token value. Create a new Pattern's secret "github_token" 
with the copied token value. Set the *github_token* parameter on this node to the newly created secret.

Set the *github_owner_username* and *github_repo_slug* parameters on 
this node. The url for a github repo follows this 
structure https://github.com/ownerUsername/repoSlug, so you can get these values from there. 

Run this node which will also run the downstream nodes
- :Node{#5gm67t4w} - outputs all of open github issues for the repo to a table
- :Node{#o6ozzrej} - outputs the body text for each of the github issues to a table
- :Node{#yurgh7ar} - outputs the embedding for each issue to a table


__Step 6. Test it out! - :Node{#5qg6ojs2}__
