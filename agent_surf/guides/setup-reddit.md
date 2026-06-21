# Reddit Setup Guide

## What it does

Reddit blocks most non-browser direct access (including datacenter and ISP proxy IPs); JSON API returns 403.

Agent Surf provides Reddit search and reading via **rdt-cli**:
- **Search:** `rdt search "query"`
- **Read full post + comments:** `rdt read POST_ID`

Free, no proxy required, no API key. Requires login (`rdt login`, auto-extracts browser cookies).

## Steps the Agent can automate

1. Check if rdt-cli is available:
```bash
which rdt && echo "installed" || echo "not installed"
```

2. If not installed, install from GitHub (PyPI lags):
```bash
pipx install 'git+https://github.com/public-clis/rdt-cli.git'
```

Or one-shot:
```bash
agent-surf install --env=auto --channels=reddit
```

## Usage examples

Search Reddit:
```bash
rdt search "python best practices" -n 5
```

Read full post and comments:
```bash
rdt read POST_ID
```

## Manual steps for the user

None. rdt-cli installs automatically via `agent-surf install --env=auto`.

## Fallback: Exa search

If Exa is configured (via mcporter), you can also search Reddit:

```bash
mcporter call 'exa.web_search_exa(query: "python best practices", numResults: 5, includeDomains: ["reddit.com"])'
```

rdt-cli is the recommended path — works without extra setup.
