# Troubleshooting

## StockTwits: community streams return errors

**Symptom:** `agent-surf doctor` shows StockTwits ⚠️, or symbol streams return HTTP 403/429.

**Cause:** StockTwits tightens its public API periodically (rate limits / occasional IP blocks). Quotes do **not** depend on StockTwits.

**Fix:** Real-time quotes still work via Yahoo Finance with no key:

```bash
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1d"
```

For community streams, wait a few minutes and retry, or route through a proxy if your IP is blocked. `agent-surf doctor` reports the live status.

---

## Twitter/X: twitter-cli connection failed

**Symptom:** `twitter search` or other commands return errors

**Cause:** twitter-cli needs AUTH_TOKEN and CT0 environment variables to access the Twitter API. If your network needs a proxy to reach x.com, configure one.

**Fix:**

### Option 1: Environment variable proxy

```bash
export HTTP_PROXY="http://user:pass@host:port"
export HTTPS_PROXY="http://user:pass@host:port"
twitter search "test" -n 1
```

### Option 2: Global proxy tool

Let a proxy tool handle all traffic so twitter-cli requests go through it:

```bash
# macOS — enable "Enhanced Mode" in ClashX / Surge
# Linux — proxychains or tun2socks
proxychains twitter search "test" -n 1
```

### Option 3: Skip twitter-cli, use Exa search instead

When twitter-cli is unavailable, search Twitter content via Exa:

```bash
mcporter call 'exa.web_search_exa(query: "site:x.com search term", numResults: 5)'
```

### Option 4: Check authentication

```bash
twitter check
```

> If it returns "Missing credentials", set AUTH_TOKEN and CT0 environment variables.
>
> **Fallback:** If you have bird CLI installed (`npm install -g @steipete/bird`), it works too. Agent Surf auto-detects installed tools.
