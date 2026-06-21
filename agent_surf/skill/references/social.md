# Social Media & Communities

Hacker News, Twitter/X, Product Hunt, StockTwits, Reddit.

## Hacker News (public API, zero config)

No auth required. Stories, items, and full-text search come from the Algolia HN
API; user profiles from the official Firebase API.

### Front-page / top stories

```bash
curl -s "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=20"
```

### Full-text search (stories)

```bash
curl -s "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=20"
# Most recent first instead of by relevance:
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=QUERY&tags=story"
```

### Story detail + nested comments (single call)

```bash
# item id comes from a news.ycombinator.com/item?id=<id> URL
curl -s "https://hn.algolia.com/api/v1/items/ITEM_ID"
```

### User profile

```bash
curl -s "https://hacker-news.firebaseio.com/v0/user/USERNAME.json"
```

### Python example

```python
from agent_surf.channels.hackernews import HackerNewsChannel

ch = HackerNewsChannel()
for s in ch.get_top_stories(limit=10):
    print(f"{s['points']:>4}  {s['title']}  ({s['num_comments']} comments)")

hits = ch.search("rust async", limit=10)
item = ch.get_item(38000000)          # story + nested comment tree
user = ch.get_user("pg")
```

## Twitter/X (twitter-cli)

### Stable commands

```bash
# Home timeline (most stable)
twitter feed -n 20

# Read single tweet (with replies)
twitter tweet URL_OR_ID

# Read long-form / X Article
twitter article URL_OR_ID

# User timeline
twitter user-posts @username -n 20

# User profile
twitter user @username
```

### Possibly unstable commands

```bash
# Search tweets (Twitter frequently changes GraphQL endpoints — may 404)
twitter search "query" -n 10

# Likes (since 2024 only your own — platform limit)
twitter likes
```

### Search failure retry chain (execute in order, stop on success)

1. Retry once (transient failures common): `twitter search "query" -n 10`
2. Upgrade and retry: `pipx upgrade twitter-cli && twitter search "query" -n 10`
3. OpenCLI fallback (desktop, browser login): `opencli twitter search "query" -f yaml`
4. If all fail, use stable commands: `twitter feed` / `twitter user-posts @somebody`

### Important notes

> **Install:** `pipx install twitter-cli` (ensure v0.8.5+)
>
> **Auth:** Prefer Cookie-Editor export → set `TWITTER_AUTH_TOKEN` + `TWITTER_CT0`. Auto-extract unavailable on SSH/Docker/headless.
>
> **IP risk:** Avoid frequent calls from VPS/datacenter IPs, especially followers/following — ban risk. Use residential proxy or local environment.
>
> **OpenCLI fallback:** On desktop with OpenCLI, `opencli twitter search/article/user-posts -f yaml` full set works (browser login, no cookie env vars).
>
> **Output format:** Prefer `--yaml` or `--json` for structured output — better for AI agents.

## Product Hunt (developer token)

Product Hunt's API v2 is GraphQL and needs a free developer token.

> **Setup once:** create an app at https://www.producthunt.com/v2/oauth/applications,
> generate a developer token, then `agent-surf configure producthunt-token YOUR_TOKEN`.
> Run `agent-surf doctor --json` to confirm producthunt is `ok`.

```python
from agent_surf.channels.producthunt import ProductHuntChannel

ch = ProductHuntChannel()

# Today's top launches by votes
for p in ch.get_trending(limit=10):
    print(f"▲{p['votes']:>4}  {p['name']} — {p['tagline']}")

# Keyword filter over recent ranked launches
hits = ch.search("ai agent", limit=10)

# Full detail for one launch (slug from its producthunt.com/posts/<slug> URL)
post = ch.get_post("notion-ai")
```

> **Search note:** Product Hunt's API has no free-text post search, so `search()`
> scans a page of ranked launches and filters by name/tagline. For exhaustive
> discovery, combine with Exa `site:producthunt.com QUERY`.

## StockTwits + Yahoo Finance (US stocks & investing community)

Quotes come from Yahoo Finance (public, no key); community streams, symbol
search, and trending symbols from the public StockTwits API.

### Real-time quote (Yahoo Finance)

```bash
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1d"
```

### Trending symbols / symbol stream / search (StockTwits)

```bash
curl -s "https://api.stocktwits.com/api/2/trending/symbols.json"
curl -s "https://api.stocktwits.com/api/2/streams/symbol/TSLA.json"
curl -s "https://api.stocktwits.com/api/2/search/symbols.json?q=apple"
```

### Python example

```python
from agent_surf.channels.stocktwits import StockTwitsChannel

ch = StockTwitsChannel()
q = ch.get_stock_quote("AAPL")        # current/chg/percent/high/low/volume (Yahoo)
trending = ch.get_trending_symbols(limit=10)
posts = ch.get_symbol_stream("TSLA", limit=20)
```

> **Rate limits:** StockTwits tightens its public API periodically — if streams
> return errors, Yahoo Finance quotes still work; `agent-surf doctor` reports the
> live status. Use index tickers like `^GSPC` (S&P 500), `^IXIC` (Nasdaq).

## Reddit (multi-backend, login required)

**No zero-config path for Reddit:** anonymous `.json` endpoints blocked (403); official API approval-gated since 2025-11. Both backends need login — run `agent-surf doctor --json` for reddit's `active_backend`. Restricted networks may need a proxy.

### Backend A: OpenCLI (desktop preferred, browser login)

```bash
# Search posts
opencli reddit search "query" -f yaml

# Read full post + comments
opencli reddit read POST_ID -f yaml

# Browse subreddit / hot / Popular
opencli reddit subreddit LocalLLaMA -f yaml
opencli reddit hot -f yaml
opencli reddit popular -f yaml

# Subreddit metadata (subscribers, description)
opencli reddit subreddit-info LocalLLaMA -f yaml
```

> Requires Chrome open and logged into reddit.com in browser.

### Backend B: rdt-cli (legacy/server fallback, upstream unmaintained since 2026-03)

```bash
rdt search "query" --limit 10   # Search posts
rdt read POST_ID                # Read full post + comments
rdt sub python --limit 20       # Browse subreddit
rdt popular --limit 10          # Browse hot
rdt all --limit 10              # Browse /r/all
```

> **Install:** `pipx install 'git+https://github.com/public-clis/rdt-cli.git'` (PyPI lags — need GitHub v0.4.2+). Run `rdt login` before search/read (on headless servers write cookies manually per doctor hints).
> Prefer `--yaml` output for AI agents.

### Advanced: Official API + PRAW (existing credentials only)

Users who registered a Reddit script app before 2025-11 (with client_id/client_secret) can use PRAW (100 QPM free). New applications require manual approval and personal projects are rarely approved — **do not recommend for new users**.
