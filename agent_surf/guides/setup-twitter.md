# Twitter Advanced Features Setup Guide (twitter-cli)

Basic Twitter reading works free via Jina Reader — no setup needed.

Advanced features need twitter-cli (@public-clis/twitter-cli):

- Search tweets (`twitter search`)
- Read full tweets and threads (`twitter tweet`, `twitter thread`)
- User timeline (`twitter timeline`)
- Long-form articles (`twitter article`)

twitter-cli is free and open source (pipx install) but needs your Twitter account cookies.

## Quick setup

1. Check if twitter-cli is installed:

```bash
which twitter && echo "installed" || echo "not installed"
```

2. Install twitter-cli:

```bash
pipx install twitter-cli
```

3. Test configuration:

```bash
twitter search "test" -n 1
```

## Get cookies (Cookie-Editor method, recommended)

1. Install [Cookie-Editor](https://cookie-editor.com/) browser extension
2. Log into x.com
3. Click Cookie-Editor icon → Export → copy all
4. Run configure command:

```bash
agent-surf configure twitter-cookies "PASTED_COOKIE_JSON"
```

This auto-extracts `auth_token` and `ct0` and writes env vars.

## Manual cookie setup

If you already have `auth_token` and `ct0`:

1. Install twitter-cli if missing: `pipx install twitter-cli`

2. Set environment variables:

```bash
export AUTH_TOKEN="your_auth_token"
export CT0="your_ct0"
```

3. Test:

```bash
twitter search "test" -n 1
```

## Proxy configuration

> twitter-cli supports proxy via environment variables:

```bash
export HTTP_PROXY="http://user:pass@host:port"
export HTTPS_PROXY="http://user:pass@host:port"
twitter search "test" -n 1
```

Or use a global proxy tool:

```bash
proxychains twitter search "test" -n 1
```

## Fallback: bird CLI

If you have [bird CLI](https://www.npmjs.com/package/@steipete/bird) installed (`npm install -g @steipete/bird`), it works too. Agent Surf auto-detects bird. Both are similar; twitter-cli is the current recommendation.
