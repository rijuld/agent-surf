# -*- coding: utf-8 -*-
"""Hacker News — public API channel for stories, comments, and users.

User profiles come from the official Firebase API; stories, item detail, and
full-text search come from the Algolia HN Search API (a single Algolia call
returns nested comments and rich metadata, avoiding the N+1 item lookups the
raw Firebase API would require).
"""

import json
import urllib.parse
import urllib.request
from typing import Any

from .base import Channel

_UA = "agent-surf/1.0"
_TIMEOUT = 10
_FIREBASE = "https://hacker-news.firebaseio.com/v0"
_ALGOLIA = "https://hn.algolia.com/api/v1"


def _get_json(url: str) -> Any:
    """Fetch *url* and return parsed JSON. Raises on HTTP/network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


class HackerNewsChannel(Channel):
    name = "hackernews"
    description = "Hacker News stories, comments, and users"
    backends = ["HN API (public)"]
    tier = 0

    # ------------------------------------------------------------------ #
    # URL routing
    # ------------------------------------------------------------------ #

    def can_handle(self, url: str) -> bool:
        d = urllib.parse.urlparse(url).netloc.lower()
        return "news.ycombinator.com" in d or "hn.algolia.com" in d

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    def check(self, config=None):
        try:
            _get_json(f"{_FIREBASE}/topstories.json")
            self.active_backend = self.backends[0]
            return "ok", (
                "Public API available (top/new/best stories, item + comments, "
                "user profiles, full-text search)"
            )
        except Exception as e:
            self.active_backend = None
            return "warn", f"Hacker News API connection failed (proxy may be required): {e}"

    # ------------------------------------------------------------------ #
    # Data-fetching methods
    # ------------------------------------------------------------------ #

    @staticmethod
    def _story(hit: dict) -> dict:
        """Normalize an Algolia story hit into a flat dict."""
        object_id = hit.get("objectID", "")
        return {
            "id": int(object_id) if str(object_id).isdigit() else 0,
            "title": hit.get("title") or hit.get("story_title") or "",
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
            "author": hit.get("author", ""),
            "points": hit.get("points", 0),
            "num_comments": hit.get("num_comments", 0),
            "created_at": hit.get("created_at", ""),
        }

    def get_top_stories(self, limit: int = 20) -> list:
        """Front-page stories.

        Returns a list of dicts with keys:
          id, title, url, author, points, num_comments, created_at
        """
        data = _get_json(f"{_ALGOLIA}/search?tags=front_page&hitsPerPage={limit}")
        return [self._story(h) for h in (data.get("hits") or [])[:limit]]

    def get_item(self, item_id: int) -> dict:
        """Single story (or comment) detail with its nested comment tree.

        Args:
            item_id: HN item id (from a news.ycombinator.com/item?id=<id> URL)

        Returns a dict with keys:
          id, title, url, text, author, points, created_at,
          children (recursive list of {id, author, text, created_at, children})
        """
        item = _get_json(f"{_ALGOLIA}/items/{item_id}")

        def _flatten(node: dict) -> list:
            out = []
            for c in (node.get("children") or []):
                out.append(
                    {
                        "id": c.get("id", 0),
                        "author": c.get("author", "") or "",
                        "text": c.get("text", "") or "",
                        "created_at": c.get("created_at", ""),
                        "children": _flatten(c),
                    }
                )
            return out

        return {
            "id": item.get("id", item_id),
            "title": item.get("title", "") or "",
            "url": item.get("url") or f"https://news.ycombinator.com/item?id={item_id}",
            "text": item.get("text", "") or "",
            "author": item.get("author", "") or "",
            "points": item.get("points", 0),
            "created_at": item.get("created_at", ""),
            "children": _flatten(item),
        }

    def get_user(self, username: str) -> dict:
        """User profile via the Firebase API.

        Returns a dict with keys:
          id, karma, about, created, submitted_count, url
        """
        data = _get_json(f"{_FIREBASE}/user/{urllib.parse.quote(username)}.json") or {}
        uid = data.get("id", username)
        return {
            "id": uid,
            "karma": data.get("karma", 0),
            "about": data.get("about", "") or "",
            "created": data.get("created", 0),
            "submitted_count": len(data.get("submitted") or []),
            "url": f"https://news.ycombinator.com/user?id={uid}",
        }

    def search(self, query: str, limit: int = 10) -> list:
        """Full-text story search via Algolia.

        Returns a list of dicts with keys:
          id, title, url, author, points, num_comments, created_at
        """
        url = (
            f"{_ALGOLIA}/search?query={urllib.parse.quote(query)}"
            f"&tags=story&hitsPerPage={limit}"
        )
        data = _get_json(url)
        return [self._story(h) for h in (data.get("hits") or [])[:limit]]
