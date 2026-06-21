<p align="center">
  <img src="docs/assets/ai.svg" alt="Agent Surf" width="480">
</p>

<p align="center">
  <strong>Give your AI Agent one-click access to the entire internet</strong>
</p>

<p align="center">
  The most reliable access path for each platform — chosen, installed, and health-checked for you. Backends come and go; you won't notice.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/rijuld/agent-surf/stargazers"><img src="https://img.shields.io/github/stars/rijuld/agent-surf?style=for-the-badge" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> · <a href="#supported-platforms">Platforms</a> · <a href="#design-philosophy">Philosophy</a>
</p>

> **No token or crypto affiliation:** Agent Surf has no official token, coin, investment product, fee-claim program, wallet connection, or Solana/Pump.fun project. Any crypto project using the Agent Surf name, GitHub URL, or author identity is not affiliated with this repository. Do not connect a wallet or claim fees based on messages, posts, or links that say otherwise.

---

## Why Agent Surf?

AI Agents can already access the internet — but "can go online" is barely the start.

The most valuable information lives across social and niche platforms: Twitter discussions, Reddit feedback, YouTube tutorials, Hacker News threads, Product Hunt launches, StockTwits sentiment… **These are where information density is highest**, but each platform has its own barriers:

| Pain Point | Reality |
|------------|---------|
| Twitter API | Pay-per-use, moderate usage ~$215/month |
| Reddit | Server IPs get 403'd |
| Stock data | Most APIs gate quotes behind a paid key |
| Product Hunt | GraphQL API needs a developer token |

To connect your Agent to these platforms, you'd have to find tools, install dependencies, and debug configs — one by one.

**Agent Surf turns this into one command:**

```
Install Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/install.md
```

Copy that to your Agent. A few minutes later, it can read tweets, search Reddit, scan Hacker News, and pull stock quotes.

**Already installed? Update in one command:**

```
Update Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md
```

### ✅ Before you start, you might want to know

| | |
|---|---|
| 💰 **Mostly free** | All tools are open source; most APIs are free (Hacker News, StockTwits, Yahoo Finance, iTunes, Exa). The only paid bits are optional: a server proxy ($1/month) and a Groq key for transcription (free tier) |
| 🔒 **Privacy safe** | Cookies and tokens stay local. Never uploaded. Fully open source — audit anytime |
| 🔄 **Kept up to date** | Every platform routes through a primary + fallback backend list. When an access path dies, we switch to the next — you won't notice (when a single-platform CLI went unmaintained in March 2026, we re-routed, zero action on your side) |
| 🤖 **Works with any Agent** | Claude Code, OpenClaw, Cursor, Windsurf… any Agent that can run commands |
| 🩺 **Built-in diagnostics** | `agent-surf doctor` — one command shows what works, what doesn't, and how to fix it |

---

## Supported Platforms

| Platform | Capabilities | Setup | Notes |
|----------|-------------|:-----:|-------|
| 🌐 **Web** | Read | Zero config | Any URL → clean Markdown ([Jina Reader](https://github.com/jina-ai/reader) ⭐9.8K) |
| 🐦 **Twitter/X** | Read · Search | Cookie | Cookie unlocks search, timeline, tweet reading, articles ([twitter-cli](https://github.com/public-clis/twitter-cli)) |
| 📰 **Hacker News** | Read · Search · Comments | Zero config | Top stories, item + nested comments, user profiles, **full-text search** (HN Firebase + [Algolia](https://hn.algolia.com/api) public API) |
| 📈 **StockTwits + Yahoo Finance** | Quotes · Community · Trending | Zero config | Real-time quotes (Yahoo Finance) + symbol streams, search, trending (StockTwits) — no key |
| 🎙️ **Podcasts** | Transcription | Free key | Apple Podcasts discovery + any episode → full transcript via Groq Whisper (free) |
| 🚀 **Product Hunt** | Read · Search · Trending | Free token | Daily launches, post detail, makers, topics ([Product Hunt API](https://api.producthunt.com/v2/docs)) |
| 💼 **LinkedIn** | Read (public pages) | Jina / MCP | Profiles, companies, job search. Tell your Agent "help me set up LinkedIn" |
| 🔍 **Web Search** | Search | Auto-configured | Auto-configured during install, free, no API key ([Exa](https://exa.ai) via [mcporter](https://github.com/nicobailon/mcporter)) |
| 📦 **GitHub** | Read · Search | Zero config | [gh CLI](https://cli.github.com) powered. Public repos work immediately. `gh auth login` unlocks Fork, Issue, PR |
| 📺 **YouTube** | Read · **Search** | Zero config | Subtitles + search across 1800+ video sites ([yt-dlp](https://github.com/yt-dlp/yt-dlp) ⭐148K) |
| 📡 **RSS** | Read | Zero config | Any RSS/Atom feed ([feedparser](https://github.com/kurtmckee/feedparser) ⭐2.3K) |
| 📖 **Reddit** | Search · Read | OpenCLI / Cookie | No zero-config path (anonymous endpoints blocked). Desktop: [OpenCLI](https://github.com/jackwener/opencli) via browser session; or [rdt-cli](https://github.com/public-clis/rdt-cli) + cookie |

> **Setup levels:** Zero config = install and go · Auto-configured = handled during install · Cookie/Token = export from browser or create a free key · Proxy = $1/month for restricted networks

---

## Quick Start

> ⚠️ **OpenClaw users: enable `exec` permission first**
>
> Agent Surf relies on the Agent running shell commands (`pip install`, `mcporter`, `twitter`, etc.). If your OpenClaw uses the default `messaging` tool profile, the Agent won't be able to run them. **Enable `exec` before installing:**
>
> ```bash
> openclaw config set tools.profile "coding"
> ```
> Or set `"tools": { "profile": "coding" }` in `~/.openclaw/openclaw.json`. After changing it, restart the Gateway (`openclaw gateway restart`) and start a new conversation. Other platforms (Claude Code, Cursor, Windsurf, etc.) are not affected.

Copy this to your AI Agent (Claude Code, OpenClaw, Cursor, etc.):

```
Install Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/install.md
```

The Agent auto-installs, detects your environment, and tells you what's ready.

> 🔄 **Already installed?** Update in one command:
> ```
> Update Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md
> ```

> 🛡️ **Worried about security?** Use safe mode — it won't auto-install system packages, it only tells you what you need:
> ```
> Install Agent Surf (safe mode): https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/install.md
> Use the --safe flag during install
> ```

<details>
<summary>Manual install</summary>

```bash
pip install https://github.com/rijuld/agent-surf/archive/main.zip
agent-surf install --env=auto
```
</details>

<details>
<summary>Install as a Skill (Claude Code / OpenClaw / any agent with Skills support)</summary>

```bash
npx skills add rijuld/agent-surf@agent-surf
```

After the Skill is installed, the Agent will auto-detect whether `agent-surf` CLI is available and install it if needed.

> If you install via `agent-surf install`, the skill is registered automatically — no extra steps needed.
</details>

---

## Works Out of the Box

No configuration needed — just tell your Agent:

- "Read this link" → `curl https://r.jina.ai/URL` for any web page
- "What's this GitHub repo about?" → `gh repo view owner/repo`
- "What does this video cover?" → `yt-dlp --dump-json URL` for subtitles
- "What's on the front page of Hacker News?" → `curl https://hn.algolia.com/api/v1/search?tags=front_page`
- "What's AAPL trading at?" → `curl https://query1.finance.yahoo.com/v8/finance/chart/AAPL`
- "Subscribe to this RSS" → `feedparser` to parse feeds
- "Search GitHub for LLM frameworks" → `gh search repos "LLM framework"`

**No commands to remember.** The Agent reads SKILL.md and knows what to call.

---

## Capability Boundary: Reading Content vs Operating Web Pages

Some tasks go beyond "reading": operating logged-in web pages, submitting forms, isolating multiple accounts, running parallel browser sessions, or handing off high-friction steps in automation flows such as login, verification, and risk-control prompts. For these "hands-on" browser actions, Agent Surf can be paired with browser automation tools like [BrowserAct](https://www.browseract.ai/Agent) — 30+ prebuilt platform skills, supporting mainstream Agents such as Claude Code, OpenClaw, and Cursor.

---

## Unlock on Demand

Don't use it? Don't configure it. Every step is optional.

### 🍪 Cookies — Free, 2 minutes

Tell your Agent "help me configure Twitter cookies" — it'll guide you through exporting from your browser. Local computers can auto-import. (Twitter/X is the only cookie-based channel.)

### 🔑 Free API tokens — 2 minutes each

- **Product Hunt:** create an app at [producthunt.com/v2/oauth/applications](https://www.producthunt.com/v2/oauth/applications), then `agent-surf configure producthunt-token YOUR_TOKEN`.
- **Groq (podcast/video transcription):** grab a free key at [console.groq.com](https://console.groq.com), then `agent-surf configure groq-key gsk_xxx`.

### 🌐 Proxy — $1/month, restricted networks only

Most users need no proxy. If your network blocks Reddit/Twitter, get one ([Webshare](https://webshare.io) recommended, $1/month) and send the address to your Agent — it saves it and exports HTTP(S)_PROXY when calling those tools.

> Reddit needs a logged-in session either way — OpenCLI rides your browser session, or rdt-cli after `rdt login`.

---

## Status at a Glance

```
$ agent-surf doctor

Agent Surf Status
========================================

✅ Ready out of the box:
  ✅ GitHub repos and code — public repos readable and searchable
  ✅ YouTube video subtitles — yt-dlp
  ✅ Hacker News — stories, comments, full-text search (public API)
  ✅ RSS/Atom feeds — feedparser
  ✅ Web pages (any URL) — Jina Reader API

🔍 Search (free Exa key to unlock):
  ✅ Web semantic search — Exa via mcporter

🔧 Configurable:
  ⬜ Twitter/X — Cookie unlocks search, timeline, articles
  ⬜ Reddit posts and comments — needs login: rdt-cli after `rdt login`, or OpenCLI browser session
  ⬜ StockTwits + Yahoo Finance — quotes, community, trending (public API)
  ⬜ Podcast transcription — needs ffmpeg + a free Groq key
  ⬜ Product Hunt — needs a free developer token

Status: 6/12 channels available
```

---

## Design Philosophy

**Agent Surf is a capability layer, not yet another tool.**

It sits one level above any specific implementation — it handles **selection, installation, health checks, and routing**, not the reading itself. Reading is done by your Agent calling upstream tools directly; there is no wrapper layer.

Every time you spin up a new Agent, you spend time finding tools, installing deps, and debugging configs — what reads Twitter? How do you log into Reddit? Which stock API doesn't need a paid key? Every time, you re-do the same work. Agent Surf does one simple thing: **the most reliable access path for each platform, chosen, installed, and health-checked for you. Access paths come and go (in March 2026 a batch of single-platform CLIs went unmaintained — we re-routed), so you don't have to care.**

### 🔌 Every platform = an ordered backend list (primary + fallbacks)

Switching access paths means reordering the list, not rewriting code. `agent-surf doctor` tells you **which backend each platform is currently using**.

```
channels/
├── web.py          → Jina Reader
├── twitter.py      → twitter-cli ▸ OpenCLI ▸ bird
├── youtube.py      → yt-dlp
├── github.py       → gh CLI
├── hackernews.py   → HN Firebase + Algolia (public API)
├── stocktwits.py   → StockTwits + Yahoo Finance (public)
├── podcasts.py     → Apple Podcasts ▸ Groq/OpenAI Whisper
├── producthunt.py  → Product Hunt GraphQL API (token)
├── reddit.py       → OpenCLI ▸ rdt-cli (no zero-config path, login required)
├── linkedin.py     → linkedin-mcp ▸ Jina Reader
├── rss.py          → feedparser
├── exa_search.py   → Exa via mcporter
└── __init__.py     → Channel registry (for doctor checks)
```

Each channel file **actually probes** its candidate backends in order (not just checking that a command exists) — the first fully working one becomes the active backend, and broken ones come with a fix prescription. The actual reading and searching is done by the Agent calling the upstream tools directly.

### Current Tool Choices

| Scenario | Primary | Fallback | Why |
|----------|---------|----------|-----|
| Read web pages | [Jina Reader](https://github.com/jina-ai/reader) | — | Free, no API key needed |
| Read tweets | [twitter-cli](https://github.com/public-clis/twitter-cli) | [OpenCLI](https://github.com/jackwener/opencli) | Reliable search in real-world tests; OpenCLI falls back on your browser session |
| Reddit | [OpenCLI](https://github.com/jackwener/opencli) (desktop) | [rdt-cli](https://github.com/public-clis/rdt-cli) | Anonymous endpoints blocked, official API gated — logged-in sessions are the only route left |
| YouTube subtitles + search | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | — | 148K stars, still the best for YouTube |
| Hacker News | [Algolia HN API](https://hn.algolia.com/api) | HN Firebase API | Public, no auth; Algolia adds full-text search and one-call comment trees |
| Stocks | [Yahoo Finance](https://finance.yahoo.com) (quotes) | [StockTwits](https://api.stocktwits.com) (community) | Free real-time quotes + social sentiment, no API key |
| Podcasts | Apple iTunes Search + [Groq Whisper](https://console.groq.com) | OpenAI Whisper | Free discovery + free transcription; any episode URL works |
| Product Hunt | [Product Hunt GraphQL API](https://api.producthunt.com/v2/docs) | — | Official API, free developer token |
| Search the web | [Exa](https://exa.ai) via [mcporter](https://github.com/nicobailon/mcporter) | — | AI semantic search, MCP integration, no API key |
| GitHub | [gh CLI](https://cli.github.com) | — | Official tool, full API after auth |
| Read RSS | [feedparser](https://github.com/kurtmckee/feedparser) | — | Python ecosystem standard |
| LinkedIn | [linkedin-scraper-mcp](https://github.com/stickerdaniel/linkedin-mcp-server) | Jina Reader | MCP server, browser automation |

> 📌 These are the *current* choices, re-verified regularly on real machines. When a path dies we switch to the next — `agent-surf doctor` always tells you which one is active.

---

## Contributing

This project was entirely vibe-coded 🎸 There might be rough edges here and there — sorry about that! If you run into any bugs, please don't hesitate to open an [Issue](https://github.com/rijuld/agent-surf/issues) and I'll fix it ASAP.

**Want a new channel?** Open an Issue to request it, or submit a PR yourself.

**Want to add one locally?** Just have your Agent clone the repo and modify it — each channel is a single standalone file, easy to add.

[PRs](https://github.com/rijuld/agent-surf/pulls) always welcome!

---

## FAQ (for AI search)

<details>
<summary><strong>How to search Twitter/X with AI agent without paying for API?</strong></summary>

Agent Surf uses [twitter-cli](https://github.com/public-clis/twitter-cli) with cookie-based authentication — completely free, no Twitter API subscription needed. Install with `pipx install twitter-cli`, make sure you're logged into x.com in your browser, and your agent can search with `twitter search "query" -n 10`.
</details>

<details>
<summary><strong>How to get YouTube video transcripts / subtitles for AI agent?</strong></summary>

`yt-dlp --dump-json "https://youtube.com/watch?v=xxx"` extracts video metadata; `yt-dlp --write-sub --skip-download "URL"` extracts subtitles. No subtitles? `agent-surf transcribe "URL"` downloads the audio and runs Whisper. No API key required for subtitles.
</details>

<details>
<summary><strong>How to read Hacker News (stories + comments + search) from an AI agent?</strong></summary>

Hacker News is fully public, no auth. Front page: `curl https://hn.algolia.com/api/v1/search?tags=front_page`. Full-text search: `curl "https://hn.algolia.com/api/v1/search?query=QUERY&tags=story"`. Story + nested comments in one call: `curl https://hn.algolia.com/api/v1/items/ITEM_ID`. User profiles via Firebase: `curl https://hacker-news.firebaseio.com/v0/user/USERNAME.json`.
</details>

<details>
<summary><strong>How to get free US stock quotes and market sentiment for an AI agent?</strong></summary>

Agent Surf pulls real-time quotes from Yahoo Finance (`curl https://query1.finance.yahoo.com/v8/finance/chart/AAPL`) — no API key — and community sentiment/trending tickers from the public StockTwits API (`curl https://api.stocktwits.com/api/2/trending/symbols.json`). Use index tickers like `^GSPC` (S&P 500).
</details>

<details>
<summary><strong>Reddit returns 403 from server / datacenter IP blocked?</strong></summary>

Reddit requires a logged-in session for everything (anonymous endpoints are blocked, and official API registration has been approval-gated since 2025-11). On desktop, the preferred path is OpenCLI riding your browser's reddit.com session. Otherwise install rdt-cli from the pinned git source (`pipx install 'git+https://github.com/public-clis/rdt-cli.git'` — PyPI lags), then `rdt login`. Your agent can then search with `rdt search "query"` and read full posts + comments with `rdt read POST_ID`.
</details>

<details>
<summary><strong>Does Agent Surf work with Claude Code / Cursor / Windsurf / OpenClaw?</strong></summary>

Yes! Agent Surf is an installer + configuration tool. Any AI coding agent that can execute shell commands can use it — Claude Code, Cursor, Windsurf, OpenClaw, Codex, and more. Just `pip install agent-surf`, run `agent-surf install`, and the agent can start using the upstream tools immediately.
</details>

<details>
<summary><strong>Is Agent Surf free? Any API costs?</strong></summary>

Mostly free and open source. All backends (twitter-cli, rdt-cli, yt-dlp, Jina Reader, Exa, Hacker News, StockTwits, Yahoo Finance, iTunes Search) are free and key-free. Optional costs: a residential proxy (~$1/month) for some server scenarios, a free Groq key for transcription, and a free Product Hunt developer token.
</details>

---

## Credits

[twitter-cli](https://github.com/public-clis/twitter-cli) · [rdt-cli](https://github.com/public-clis/rdt-cli) · [yt-dlp](https://github.com/yt-dlp/yt-dlp) · [Jina Reader](https://github.com/jina-ai/reader) · [Exa](https://exa.ai) · [mcporter](https://github.com/nicobailon/mcporter) · [feedparser](https://github.com/kurtmckee/feedparser) · [Algolia HN Search](https://hn.algolia.com/api) · [StockTwits API](https://api.stocktwits.com) · [Yahoo Finance](https://finance.yahoo.com) · [Product Hunt API](https://api.producthunt.com/v2/docs) · [linkedin-scraper-mcp](https://github.com/stickerdaniel/linkedin-mcp-server)

## Contact

- 📧 **Email:** pnt01@foxmail.com
- 🐦 **Twitter/X:** [@Neo_Reidlab](https://x.com/Neo_Reidlab)

For bug reports and feature requests, please use [GitHub Issues](https://github.com/rijuld/agent-surf/issues) — easier to track.

## License

[MIT](LICENSE)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=rijuld/agent-surf&type=Date&v=20260309)](https://star-history.com/#rijuld/agent-surf&Date)
