# Exa Search Setup Guide

## What it does
Exa is an AI semantic search engine. Connected via MCP — **free, no API key**. After setup you get:
- Web semantic search
- Reddit search (via site:reddit.com)
- Twitter search (via site:x.com)

## Steps the Agent can automate

`agent-surf install --env=auto` completes these automatically — usually no manual steps.

### 1. Install mcporter
```bash
npm install -g mcporter
```

### 2. Register Exa MCP
```bash
mcporter config add exa https://mcp.exa.ai/mcp
```

### 3. Verify
```bash
agent-surf doctor | grep "Search"
mcporter call 'exa.web_search_exa(query: "test", numResults: 1)'
```

## Manual steps for the user

**None.** Exa connects via MCP — free, no signup, no API key.

If `agent-surf install` didn't configure Exa due to network issues, run the two commands above manually.

## FAQ

**Q: Are there search rate limits?**
A: The MCP endpoint is provided by Exa (mcp.exa.ai) and is currently free with no hard limits. If that changes, agent-surf updates will adapt.

**Q: What is mcporter?**
A: A command-line bridge for the MCP protocol, used to call MCP servers. Agent Surf uses it for Exa search.
