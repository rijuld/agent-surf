# -*- coding: utf-8 -*-
"""Product Hunt — daily product launches and discovery (GraphQL API v2).

Product Hunt's API requires a free developer token (Bearer). check() looks for
``producthunt_token`` in config/env and degrades to ``warn`` with setup steps
when absent — the same way the cookie/login channels report a missing
credential. The API has no free-text post search endpoint, so search() pulls a
page of ranked launches and filters them client-side by name/tagline.
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Optional

from agent_surf.config import Config

from .base import Channel

_UA = "agent-surf/1.0"
_TIMEOUT = 15
_GRAPHQL = "https://api.producthunt.com/v2/api/graphql"
_TOKEN_URL = "https://www.producthunt.com/v2/oauth/applications"


def _token(config=None) -> Optional[str]:
    """Resolve the Product Hunt developer token (env first, then config)."""
    tok = os.environ.get("PRODUCTHUNT_TOKEN")
    if tok:
        return tok
    try:
        cfg = config if config is not None else Config()
        return cfg.get("producthunt_token") or None
    except Exception:
        return None


def _graphql(query: str, token: str, variables: Optional[dict] = None) -> Any:
    """POST a GraphQL query with the Bearer token; return parsed JSON."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        _GRAPHQL,
        data=body,
        headers={
            "User-Agent": _UA,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


_POST_FIELDS = """
  id name tagline votesCount commentsCount url
  topics { edges { node { name } } }
"""


def _post_node(node: dict) -> dict:
    """Normalize a Product Hunt post node into a flat dict."""
    topic_edges = ((node.get("topics") or {}).get("edges")) or []
    topics = [(t.get("node") or {}).get("name", "") for t in topic_edges]
    return {
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "tagline": node.get("tagline", ""),
        "votes": node.get("votesCount", 0),
        "comments": node.get("commentsCount", 0),
        "url": node.get("url", ""),
        "topics": [t for t in topics if t],
    }


class ProductHuntChannel(Channel):
    name = "producthunt"
    description = "Product Hunt launches and discovery"
    backends = ["Product Hunt API (token)"]
    tier = 1

    _NO_TOKEN = (
        "Product Hunt token not configured. Run: "
        "agent-surf configure producthunt-token YOUR_TOKEN"
    )

    # ------------------------------------------------------------------ #
    # URL routing
    # ------------------------------------------------------------------ #

    def can_handle(self, url: str) -> bool:
        return "producthunt.com" in urllib.parse.urlparse(url).netloc.lower()

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    def check(self, config=None):
        self.active_backend = None
        token = _token(config)
        if not token:
            return "warn", (
                "Product Hunt API token required (free). Steps:\n"
                f"  1. Create an app at {_TOKEN_URL}\n"
                "  2. Generate a developer token\n"
                "  3. Run: agent-surf configure producthunt-token YOUR_TOKEN"
            )
        try:
            data = _graphql("{ viewer { user { username } } }", token)
            if data.get("errors"):
                msg = (data["errors"][0] or {}).get("message", "unknown error")
                return "warn", f"Product Hunt token rejected: {msg}"
            self.active_backend = self.backends[0]
            return "ok", "Fully available (trending launches, post detail, keyword search)"
        except Exception as e:
            return "warn", f"Product Hunt API connection failed: {e}"

    # ------------------------------------------------------------------ #
    # Data-fetching methods
    # ------------------------------------------------------------------ #

    def get_trending(self, limit: int = 10, config=None) -> list:
        """Top launches ordered by votes.

        Returns a list of dicts with keys:
          id, name, tagline, votes, comments, url, topics
        """
        token = _token(config)
        if not token:
            return [{"error": self._NO_TOKEN}]
        query = (
            "query($n: Int!) { posts(order: VOTES, first: $n) { edges { node {"
            + _POST_FIELDS
            + "} } } }"
        )
        data = _graphql(query, token, {"n": limit})
        edges = (((data.get("data") or {}).get("posts") or {}).get("edges")) or []
        return [_post_node(e.get("node") or {}) for e in edges[:limit]]

    def search(self, query: str, limit: int = 10, config=None) -> list:
        """Keyword search over recent ranked launches (client-side filter).

        Product Hunt API v2 has no free-text post search, so this scans a page
        of ranked posts and keeps those whose name/tagline contains *query*.

        Returns a list of dicts with keys:
          id, name, tagline, votes, comments, url, topics
        """
        token = _token(config)
        if not token:
            return [{"error": self._NO_TOKEN}]
        gql = (
            "query { posts(order: RANKING, first: 50) { edges { node {"
            + _POST_FIELDS
            + "} } } }"
        )
        data = _graphql(gql, token)
        edges = (((data.get("data") or {}).get("posts") or {}).get("edges")) or []
        needle = query.lower()
        results = []
        for e in edges:
            node = _post_node(e.get("node") or {})
            if needle in node["name"].lower() or needle in node["tagline"].lower():
                results.append(node)
            if len(results) >= limit:
                break
        return results

    def get_post(self, slug: str, config=None) -> dict:
        """Full detail for a single launch by slug (from its producthunt.com URL).

        Returns a dict with keys:
          id, name, tagline, description, votes, comments, url, website,
          topics, makers
        """
        token = _token(config)
        if not token:
            return {"error": self._NO_TOKEN}
        query = (
            "query($slug: String!) { post(slug: $slug) {"
            + _POST_FIELDS
            + " description website makers { name } } }"
        )
        data = _graphql(query, token, {"slug": slug})
        node = (data.get("data") or {}).get("post") or {}
        result = _post_node(node)
        result["description"] = node.get("description", "") or ""
        result["website"] = node.get("website", "") or ""
        result["makers"] = [m.get("name", "") for m in (node.get("makers") or [])]
        return result
