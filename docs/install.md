# Agent Surf — Installation Guide

## For Humans

Copy this to your AI Agent:

```
Install Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/install.md
```

> 🛡️ **Security-conscious?** Use safe mode — it won't auto-install system packages:
> ```
> Install Agent Surf (safe mode): https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/install.md
> Use the --safe flag during install
> ```

---

## For AI Agents

### Goal

Install Agent Surf and all upstream tools so your user's agent has full internet access. After installation, you'll use the upstream tools directly (OpenCLI, twitter-cli, rdt-cli, yt-dlp, mcporter, gh CLI, public APIs, etc.) — Agent Surf is the selector, installer, health checker and router, never a wrapper.

### ⚠️ Boundaries

When fixing issues, stay within these limits:

- **DO NOT** run commands with `sudo` unless the user explicitly approved
- **DO NOT** modify system files outside `~/.agent-surf/`
- **DO NOT** install packages not listed in this guide
- **DO NOT** disable firewalls, security settings, or system protections
- **DO NOT** clone repos, create files, or run commands inside the agent workspace / working directory
- If something requires elevated permissions, **tell the user** what's needed and let them decide

### 📁 Directory Rules

All Agent Surf files go in dedicated directories — **never in the agent workspace**:

| Purpose | Directory | Example |
|---------|-----------|---------|
| Config & tokens | `~/.agent-surf/` | `~/.agent-surf/config.json` |
| Upstream tool repos | `~/.agent-surf/tools/` | `~/.agent-surf/tools/whisper/` |
| Temporary files | `/tmp/` | `/tmp/yt-dlp-output/` |
| Skills | `~/.openclaw/skills/agent-surf/` | SKILL.md |

**Why?** If you clone repos or create files in the workspace, it pollutes the user's project directory and can break their agent over time. Keep the workspace clean.

### Step 1: Install the basics

```bash
# Recommended: pipx (simplest)
pipx install https://github.com/rijuld/agent-surf/archive/main.zip
agent-surf install --env=auto

# If your Python is from Homebrew / you hit PEP 668 (externally-managed-environment)
# install in a virtual environment:
python3 -m venv ~/.agent-surf-venv
source ~/.agent-surf-venv/bin/activate
pip install https://github.com/rijuld/agent-surf/archive/main.zip
agent-surf install --env=auto
```

> 💡 **Windows / Microsoft Store Python alias?**
> If `python3 --version` opens the Microsoft Store, or `where python3` points to
> `...\AppData\Local\Microsoft\WindowsApps\python3.exe`, then `python3` is a Windows
> Store alias, not a usable Python install. Use Python Launcher `py -3`, or the actual
> `python.exe` from your install directory.
>
> PowerShell example:
> ```powershell
> py -3 -m venv $env:USERPROFILE\.agent-surf-venv
> $env:USERPROFILE\.agent-surf-venv\Scripts\Activate.ps1
> python -m pip install https://github.com/rijuld/agent-surf/archive/main.zip
> agent-surf install --env=auto
> ```

This installs core infrastructure (gh CLI, Node.js, mcporter, Exa search, yt-dlp config) and activates these zero-config channels:

- Web (Jina Reader), YouTube, GitHub, RSS, Exa Search, Hacker News, StockTwits

> 💡 **macOS / Homebrew Python shows `externally-managed-environment`?**
> That's PEP 668 protection, not an Agent Surf bug. Prefer `pipx install ...`, or create a `venv` first.

**Safe mode / Dry run:**

```bash
agent-surf install --env=auto --safe      # Check only, no auto-install
agent-surf install --env=auto --dry-run   # Preview what would be done
```

### Step 2: Ask the user which optional channels they want

After installing the basics, **ask the user** which additional channels they need. Present this list:

> Core channels are ready! You can now search the web, watch YouTube, read GitHub, scan Hacker News, pull stock quotes, and more.
>
> Optional channels — which do you need?
>
> - 🌟 **OpenCLI** (desktop recommended) — one install unlocks Reddit / Twitter fallback (reuses browser login, zero config; one "Add to Chrome" click)
> - 🐦 **Twitter/X** — search tweets, browse timeline (requires login cookies)
> - 🎙️ **Podcasts** — Apple Podcasts discovery + episode-to-text transcription (requires free Groq key + ffmpeg)
> - 🚀 **Product Hunt** — daily launches, search, trending (requires free developer token)
> - 📖 **Reddit** — search and read posts (login required: desktop OpenCLI or rdt-cli + cookies)
> - 💼 **LinkedIn** — profiles, job search
>
> Tell me which you want, e.g. "install Podcasts and Twitter". Or say "install everything".

Based on the user's choice, run:

```bash
agent-surf install --env=auto --channels=opencli,twitter   # Example: desktop user chose Twitter (OpenCLI fallback)
agent-surf install --env=auto --channels=all               # User wants everything
```

Supported channel names: `opencli`, `twitter`, `podcasts`, `reddit`, `linkedin`, `all` (Product Hunt only needs a token — see Step 3)

### Step 3: Fix what's broken

Run `agent-surf doctor` and check the output.

Try to get as many channels to ✅ as possible. If something failed during install or shows as ❌/⚠️ in doctor, diagnose the problem and try to fix it — but stay within the boundaries above. If a fix requires elevated permissions or system changes, ask the user first.

Only ask the user when you genuinely need their input (credentials, permissions, etc.).

### Step 3: Configure things that need user input

Some channels need credentials only the user can provide. Based on the doctor output, ask for what's missing:

> 🔒 **Security tip:** For Twitter/X (the only cookie-based channel), we recommend using a **dedicated/secondary account** rather than your main account. Cookie-based auth carries two risks:
> 1. **Account ban** — platforms may detect non-browser API calls and restrict or ban the account
> 2. **Credential exposure** — cookies grant full account access; using a secondary account limits the blast radius if credentials are ever compromised

> 🍪 **Cookie import (Twitter/X):**
>
> **Prefer Cookie-Editor import** — simplest and most reliable:
> 1. User logs into x.com in their browser
> 2. Install [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) Chrome extension
> 3. Click extension → Export → Header String
> 4. Send the exported string to the Agent
>
> **Local desktop users** can also run `agent-surf configure --from-browser chrome` for one-click extraction.

**Twitter search & posting:**
> "To unlock Twitter search, I need your Twitter cookies. Install the Cookie-Editor Chrome extension, go to x.com/twitter.com, click the extension → Export → Header String, and paste it to me."

```bash
agent-surf configure twitter-cookies "PASTED_STRING"
```

> **Proxy note (restricted networks):**
>
> twitter-cli and rdt-cli use Python; on restricted networks configure proxy via environment variables.
>
> **What you (Agent) should do:**
> 1. Confirm user saved proxy: `agent-surf configure proxy http://user:pass@ip:port`
> 2. Set env vars: `export HTTP_PROXY="..." HTTPS_PROXY="..."`
> 3. Agent Surf handles the rest — no extra user steps
>
> If user reports "fetch failed", see [troubleshooting.md](troubleshooting.md)

**Reddit (login is mandatory — no zero-config path):**
> Reddit anonymous endpoints are blocked; official API requires manual approval. Desktop users prefer OpenCLI (logged into reddit.com in browser); servers/legacy users use rdt-cli:

```bash
# PyPI lags — install from GitHub (same pinned version as _RDT_GIT_SOURCE in code)
pipx install 'git+https://github.com/public-clis/rdt-cli.git@5e4fb3720d5c174e976cd425ccc3b879d52cac66'
rdt login   # auto-extracts browser cookies; on headless servers follow doctor hints for manual cookies
```

> If your network or server IP is blocked from Reddit, use a residential proxy (e.g. https://webshare.io, ~$1/month):
> ```bash
> agent-surf configure proxy http://user:pass@ip:port
> ```

**Product Hunt (daily launches + discovery):**
> "Product Hunt needs a free developer token. Create an app at https://www.producthunt.com/v2/oauth/applications, generate a developer token, and send it to me."

```bash
agent-surf configure producthunt-token YOUR_TOKEN
```

> Then the agent can call `ProductHuntChannel.get_trending()` / `.search("query")` / `.get_post("slug")`, or query the GraphQL API at `https://api.producthunt.com/v2/api/graphql` directly.

**StockTwits + Yahoo Finance (US stocks — zero config):**
> "Stock quotes and community sentiment work out of the box — no key needed."

```bash
# Real-time quote (Yahoo Finance)
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1d"
# Trending tickers + symbol stream (StockTwits)
curl -s "https://api.stocktwits.com/api/2/trending/symbols.json"
```

> If StockTwits rate-limits community streams, Yahoo Finance quotes still work. `agent-surf doctor` shows the live status.

**Podcasts — Apple Podcasts transcription (Groq Whisper):**
> "Podcast transcription needs ffmpeg and a free Groq API key. It works on any episode URL (Apple Podcasts page, enclosure audio, or a local file)."

```bash
agent-surf install --channels podcasts   # checks ffmpeg + yt-dlp + key
agent-surf configure groq-key gsk_xxxxx
```

> **Get Groq API Key (free, no credit card, ~30 seconds):**
> 1. Open https://console.groq.com
> 2. Sign in with Google/GitHub (or register)
> 3. Left menu → API Keys → Create API Key
> 4. Copy key (starts with `gsk_`) and send to Agent
>
> **Usage:**
> User sends a podcast episode link; Agent runs:
> ```bash
> agent-surf transcribe "https://podcasts.apple.com/us/podcast/.../id...?i=EPISODE_ID"
> ```
>
> Downloads audio → transcodes/splits → Groq Whisper → full transcript.
>
> **Free tier limits:**
> - ~2 hours audio per hour (7200 seconds); wait 15 minutes after limit
> - Plenty for casual podcast listening
> - High quality (Whisper large-v3), no speaker diarization
> - Episodes over 2 hours: process in batches

**LinkedIn (optional — linkedin-scraper-mcp):**
> "Basic LinkedIn content works via Jina Reader. Full features (profiles, job search) need linkedin-scraper-mcp."

```bash
pip install linkedin-scraper-mcp
```

> **Login (requires browser UI):**
>
> linkedin-scraper-mcp uses Chromium — you need to see the browser window.
>
> - **Local desktop:** Run directly:
>   ```bash
>   linkedin-scraper-mcp --login --no-headless
>   ```
>   Browser opens — log into LinkedIn manually.
>
> - **Server (no UI):** Use VNC remote desktop:
>   ```bash
>   # 1. Install and start VNC on server (skip if already running)
>   apt install -y tigervnc-standalone-server
>   vncserver :1 -geometry 1280x720
>   
>   # 2. Connect VNC client to server-ip:5901
>   
>   # 3. In VNC desktop terminal:
>   export DISPLAY=:1
>   linkedin-scraper-mcp --login --no-headless
>   ```
>   Log in via VNC browser. Session saves to `~/.linkedin-mcp/profile/`.
>
> **After login, start MCP server:**
> ```bash
> linkedin-scraper-mcp --transport streamable-http --port 8001
> mcporter config add linkedin http://localhost:8001/mcp
> ```
>
> See https://github.com/stickerdaniel/linkedin-mcp-server

### Step 4: Final check

Run `agent-surf doctor` one final time and report the results to your user.

### Step 5: Set up daily monitoring (OpenClaw only)

If you are running inside **OpenClaw**, ask your user:

> "Agent Surf is installed. Want me to set up a daily health check? It monitors channels and new versions — only notifies you when something's wrong."

If the user agrees, create a **cron job** (daily, `sessionTarget: "isolated"`, `delivery: "announce"`) with this task:

```
Run agent-surf watch.
If output contains "All systems go", stay silent — no notification needed.
If output contains problems (❌ ⚠️) or a new version, send the full report and suggest fixes.
If a new version is available, ask if user wants to upgrade (one line for full update: Update Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md).
```

If the user wants a different agent to handle it, let them choose.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `agent-surf install --env=auto` | Install core channels (lightweight, zero-config) |
| `agent-surf install --env=auto --channels=twitter,podcasts` | Install core + optional channels |
| `agent-surf install --env=auto --channels=all` | Install everything |
| `agent-surf install --env=auto --safe` | Safe setup (no auto system changes) |
| `agent-surf install --env=auto --dry-run` | Preview what would be done |
| `agent-surf doctor` | Show channel status |
| `agent-surf watch` | Quick health + update check (for scheduled tasks) |
| `agent-surf check-update` | Check for new versions |
| `agent-surf configure twitter-cookies "..."` | Unlock Twitter search + posting |
| `agent-surf configure proxy URL` | Save proxy URL (Agent reads it to set HTTP_PROXY/HTTPS_PROXY for Reddit/Twitter — not an auto-unblock switch) |
| `agent-surf configure groq-key gsk_xxx` | Unlock podcast / video transcription |
| `agent-surf configure producthunt-token TOK` | Unlock Product Hunt launches + search |

After installation, use upstream tools directly. See SKILL.md for the full command reference:

| Platform | Upstream Tool | Example |
|----------|--------------|---------|
| Twitter/X | `twitter` (fallback `opencli`) | `twitter search "query" -n 10` |
| YouTube | `yt-dlp` | `yt-dlp --dump-json URL` |
| Hacker News | `curl` + HN/Algolia API | `curl -s "https://hn.algolia.com/api/v1/search?query=Q&tags=story"` |
| Stocks | `curl` + Yahoo/StockTwits | `curl -s "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"` |
| Reddit | `opencli` (fallback `rdt`) | `opencli reddit search "query" -f yaml` / `rdt read POST_ID` |
| GitHub | `gh` | `gh search repos "query"` |
| Web | `curl` + Jina | `curl -s "https://r.jina.ai/URL"` |
| Exa Search | `mcporter` | `mcporter call 'exa.web_search_exa(...)'` |
| Product Hunt | `curl` + GraphQL API | `curl -H "Authorization: Bearer TOK" https://api.producthunt.com/v2/api/graphql` |
| Podcasts | `agent-surf transcribe` | `agent-surf transcribe "<episode URL>"` |
| LinkedIn | `mcporter` | `mcporter call 'linkedin.get_person_profile(...)'` |
| RSS | `feedparser` | `python3 -c "import feedparser; ..."` |

> For multi-backend platforms, trust `agent-surf doctor --json` `active_backend`.
