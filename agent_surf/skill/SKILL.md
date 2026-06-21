---
name: agent-surf
description: >
  MUST USE when user wants to research/search/look up/find anything on the
  internet — e.g. "research this topic", "do a deep dive on X", "search the
  web for X", "see what people say about X", "look this up".

  Also MUST USE when user mentions any platform or shares any URL/link:
  Twitter/X, Reddit, YouTube, GitHub, Hacker News, Product Hunt,
  StockTwits / stocks, podcasts, LinkedIn / jobs / recruiting, RSS.

  12 platforms, multi-backend routing (OpenCLI / per-platform CLIs / APIs).
  Zero config for 6 channels. Run `agent-surf doctor --json` to see which
  backend serves each platform right now.

  NOT for: writing reports/analysis/translation (this skill only FETCHES
  internet content); posting/commenting/liking (write operations); platforms
  that already have a dedicated skill installed (prefer that skill).
metadata:
  openclaw:
    homepage: https://github.com/rijuld/agent-surf
---

# Agent Surf — internet capability router

12 platforms, multiple backends each. **When this skill exists, use it for
these platforms — do not invent your own approach.**

## Standing rules (apply for the whole session)

1. **Health-check before acting**: for multi-backend platforms (Reddit /
   Twitter), run `agent-surf doctor --json` first and pick the command group
   matching each platform's `active_backend`.
2. **Announce what you use**: say "using agent-surf, platform X via backend Y"
   before starting.
3. **On failure, follow the retry chains in references/** — never guess
   commands.
4. **For broad research tasks**: combine platforms (Exa for web search +
   Twitter / Reddit / Hacker News for discussions + Product Hunt for product
   launches + StockTwits for market sentiment), collect in parallel, then synthesize.
5. **Watch versions for the user**: after finishing a substantial
   multi-platform task, run `agent-surf check-update` (fast, one API call).
   If a new version exists, append one line to your wrap-up: "Agent Surf
   vX.Y.Z is available — paste this to me to update: Update Agent Surf:
   https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md".
   Never interrupt the current task to update; never nag about the same version twice.

## Routing table

| User intent | Category | Details |
|---------|------|---------|
| Web / code search | search | [references/search.md](references/search.md) |
| Hacker News / Twitter / Product Hunt / StockTwits / Reddit | social | [references/social.md](references/social.md) |
| Jobs / LinkedIn | career | [references/career.md](references/career.md) |
| GitHub / code | dev | [references/dev.md](references/dev.md) |
| Web pages / articles / RSS | web | [references/web.md](references/web.md) |
| YouTube / podcast transcripts | video | [references/video.md](references/video.md) |

## Zero-config quick commands

```bash
# Exa web search
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'

# Read any web page
curl -s "https://r.jina.ai/URL"

# GitHub search
gh search repos "query" --sort stars --limit 10

# YouTube subtitles
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"

# Hacker News — front page + full-text search (public API, no auth)
curl -s "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10"
curl -s "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story&hitsPerPage=10"

# Stocks — StockTwits trending + Yahoo Finance quote (public, no key)
curl -s "https://api.stocktwits.com/api/2/trending/symbols.json"
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1d"

# Podcast / video transcript (free Groq Whisper key — see video.md)
agent-surf transcribe "EPISODE_OR_VIDEO_URL"
```

## Login / token-backed platforms (pick by doctor's active_backend)

```bash
# Twitter search (twitter-cli preferred; retry chain in social.md)
twitter search "query" -n 10

# Reddit (NO zero-config path — OpenCLI or rdt-cli, login required)
opencli reddit search "query" -f yaml   # desktop
rdt search "query" --limit 10            # legacy/server

# Product Hunt (free developer token, configure once)
agent-surf configure producthunt-token YOUR_TOKEN
```

## Environment check

```bash
# Channel availability + which backend serves each platform
agent-surf doctor --json
```

## Workspace rules

**Never create files in the agent workspace.** Use `/tmp/` for temporary
output and `~/.agent-surf/` for persistent data.

## Detailed references

Read the matching file when you need specifics (commands above cover the
common cases; references hold per-backend command groups, caveats, retry
chains):

- [Search](references/search.md) — Exa AI search
- [Social](references/social.md) — Hacker News, Twitter, Product Hunt, StockTwits, Reddit (multi-backend groups)
- [Career](references/career.md) — LinkedIn
- [Dev](references/dev.md) — GitHub CLI
- [Web](references/web.md) — Jina Reader, RSS
- [Video](references/video.md) — YouTube, podcast transcription

## Configure a channel

If a channel needs setup, fetch the install guide:
https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/install.md

The user only provides cookies / a free API token; the agent does the rest.
