# Product Hunt Setup Guide

## What it does
Read Product Hunt daily launches, post detail (tagline, votes, makers, topics),
and keyword search via the official Product Hunt GraphQL API v2. Requires a free
developer token.

## Steps the Agent can automate

1. Check if already configured:
```bash
agent-surf doctor | grep -i "product hunt"
```

2. If the user provided a token, write it to config:
```bash
agent-surf configure producthunt-token YOUR_TOKEN
```
(or in Python: `from agent_surf.config import Config; Config().set("producthunt_token", "YOUR_TOKEN")`)

3. Test (optional) — a minimal viewer query returns 200 with a valid token:
```bash
curl -s https://api.producthunt.com/v2/api/graphql \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ viewer { user { username } } }"}'
```

## Manual steps for the user

Tell the user:

> Product Hunt access needs a free developer token.
>
> Steps:
> 1. Open https://www.producthunt.com/v2/oauth/applications
> 2. Click "Add an application", give it any name + a redirect URI (e.g. `https://localhost`)
> 3. In the application page, click "Create Token" under **Developer Token**
> 4. Copy the token and send it to me
>
> The token is read-only for public data and free.

## After receiving the token

1. Save it: `agent-surf configure producthunt-token YOUR_TOKEN`
2. Verify: `agent-surf doctor` (Product Hunt should show ✅)
3. The agent can now call:
   - `ProductHuntChannel.get_trending(limit=10)` — top launches by votes
   - `ProductHuntChannel.search("ai agent", limit=10)` — keyword filter over ranked launches
   - `ProductHuntChannel.get_post("slug")` — full detail for one launch

> **Note:** the API has no free-text post search endpoint, so `search()` scans a page of
> ranked launches and filters by name/tagline. For exhaustive discovery, combine with
> Exa: `exa.web_search_exa(query: "site:producthunt.com QUERY")`.
