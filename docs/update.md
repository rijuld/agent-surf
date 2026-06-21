# Agent Surf — Update Guide

## For Humans

Copy this to your AI Agent:

```
Update Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md
```

---

## For AI Agents

### ⚠️ Workspace Rules

**Never create files, clone repos, or run commands in the agent workspace.** Use `/tmp/` for temporary work and `~/.agent-surf/` for persistent data.

### Goal

Update Agent Surf to the latest version, refresh upstream tools, migrate from retired backends, and verify everything works. The user should not need to do anything manually (except things only a human can do, like clicking a browser-extension install button).

### Step 1: Check current version

```bash
agent-surf check-update
```

If it says "Already on the latest version", skip to Step 4 (verify). Otherwise continue.

### Step 2: Update Agent Surf package

```bash
pip install --upgrade https://github.com/rijuld/agent-surf/archive/main.zip
```

> If pip complains about `externally-managed-environment` (PEP 668), the user
> originally installed via pipx or a venv — use the matching command:
> `pipx install --force https://github.com/rijuld/agent-surf/archive/main.zip`
> or activate `~/.agent-surf-venv` first.

### Step 3: Refresh upstream tools

Run these to keep installed tools current. **Only upgrade what is already
installed — do not install new tools the user never asked for** (the one
exception: OpenCLI on desktop, see below).

```bash
# Python-based CLIs the user already has (upgrade keeps signatures fresh)
which twitter >/dev/null 2>&1 && { pipx upgrade twitter-cli 2>/dev/null || uv tool upgrade twitter-cli 2>/dev/null; }
which yt-dlp  >/dev/null 2>&1 && { pipx upgrade yt-dlp 2>/dev/null || uv tool upgrade yt-dlp 2>/dev/null || pip install -U yt-dlp 2>/dev/null; }

# rdt-cli is pinned to a git source (PyPI lags upstream) — same pin as the code's _RDT_GIT_SOURCE
which rdt >/dev/null 2>&1 && pipx install --force 'git+https://github.com/public-clis/rdt-cli.git@5e4fb3720d5c174e976cd425ccc3b879d52cac66' 2>/dev/null

# npm-based
which mcporter >/dev/null 2>&1 && npm update -g mcporter 2>/dev/null
which opencli  >/dev/null 2>&1 && npm update -g @jackwener/opencli 2>/dev/null
```

**Desktop users without OpenCLI**: OpenCLI is the preferred backend for Reddit
(and a Twitter fallback) by riding the user's browser session. Offer it once:

> "This update can use OpenCLI (reuses your browser login — zero config for Reddit). Want it? After install you only need one 'Add to Chrome' click."

If yes: `agent-surf install --channels opencli` and guide them through the
extension click. If no, everything keeps working on existing backends.

### Step 4: Coexistence (DO NOT uninstall old tools)

**Never uninstall tools the user already has.** Retired or fallback backends
(e.g. an unmaintained single-platform CLI that still functions) keep working
where they can. Agent Surf routes around them automatically — removal is the
user's call, not yours.

### Step 5: Verify

```bash
agent-surf version
agent-surf doctor
```

Running `agent-surf doctor` (text mode) also auto-syncs the bundled skill
(SKILL.md + references) into every detected agent skill directory — no
separate skill-update step is needed.

Check the doctor output:

- Every channel shows ✅ / [!] with a clear message, and multi-backend
  channels (Reddit/Twitter) report `Active backend: …`
- If a previously-working channel now shows [X]/error, the message contains
  the exact fix (e.g. a venv-reinstall prescription) — run it, then re-check
- `--json` gives the same data machine-readably (`active_backend` per channel)

### Step 6: Report to user

Tell the user:

1. What version they're on now (`agent-surf version`)
2. How many channels are available, and which backend each multi-backend
   platform is using (from doctor)
3. Anything that needs their action (e.g. Chrome extension click for OpenCLI,
   `rdt login` for Reddit, a Product Hunt token, or a Groq key for transcription)
4. What changed in this update (release notes shown by `check-update`)

Done.
