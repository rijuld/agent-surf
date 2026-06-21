# -*- coding: utf-8 -*-
"""Podcasts (Apple Podcasts) — discovery + Whisper transcription.

Discovery uses Apple's public iTunes Search API (no key). Transcription reuses
the platform-agnostic ``agent_surf.transcribe`` pipeline (yt-dlp download →
ffmpeg transcode/chunk → Groq/OpenAI Whisper) — the same path behind
``agent-surf transcribe <url>``.
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from agent_surf.config import Config
from agent_surf.probe import probe_command

from .base import Channel

_UA = "agent-surf/1.0"
_TIMEOUT = 10
_ITUNES = "https://itunes.apple.com/search"


def _get_json(url: str) -> Any:
    """Fetch *url* and return parsed JSON. Raises on HTTP/network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


class PodcastsChannel(Channel):
    name = "podcasts"
    description = "Podcast transcription (Apple Podcasts)"
    backends = ["groq-whisper", "ffmpeg"]
    tier = 1

    # ------------------------------------------------------------------ #
    # URL routing
    # ------------------------------------------------------------------ #

    def can_handle(self, url: str) -> bool:
        d = urllib.parse.urlparse(url).netloc.lower()
        return any(h in d for h in ("podcasts.apple.com", "overcast.fm", "pca.st"))

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    def check(self, config=None):
        self.active_backend = None

        # ffmpeg — really execute it: a stale pip-installed ffmpeg shim passes
        # shutil.which() but cannot run.
        probe = probe_command("ffmpeg", ["-version"], timeout=10, package="ffmpeg")
        if probe.status == "missing":
            return "off", (
                "Requires ffmpeg (audio transcoding and chunking). Install:\n"
                "  Ubuntu/Debian: apt install -y ffmpeg\n"
                "  macOS: brew install ffmpeg"
            )
        if not probe.ok:
            return "error", (
                "ffmpeg cannot execute. Reinstall: brew install ffmpeg (macOS) / apt install ffmpeg (Linux)"
            )

        # yt-dlp downloads the episode audio.
        yt = probe_command("yt-dlp", ["--version"], timeout=10, package="yt-dlp")
        if yt.status == "missing":
            return "off", "Requires yt-dlp to download episode audio. Install: pipx install yt-dlp"
        if not yt.ok:
            return "error", "yt-dlp cannot execute. Reinstall: uv tool install --force yt-dlp"

        # A Whisper provider key — Groq preferred (free), OpenAI accepted.
        has_key = bool(os.environ.get("GROQ_API_KEY")) or bool(os.environ.get("OPENAI_API_KEY"))
        if not has_key:
            try:
                cfg = config if config is not None else Config()
                has_key = bool(cfg.get("groq_api_key")) or bool(cfg.get("openai_api_key"))
            except Exception:
                has_key = False
        if not has_key:
            return "warn", (
                "Groq API key required (free). Steps:\n"
                "  1. Sign up at https://console.groq.com\n"
                "  2. Run: agent-surf configure groq-key gsk_xxxxx\n"
                "Then transcribe any episode: agent-surf transcribe <podcast episode URL>"
            )

        self.active_backend = "groq-whisper"
        return "ok", "Fully available (episode download + Whisper transcription via `agent-surf transcribe`)"

    # ------------------------------------------------------------------ #
    # Discovery + transcription
    # ------------------------------------------------------------------ #

    def search(self, query: str, limit: int = 10) -> list:
        """Search podcasts via the Apple iTunes Search API.

        Returns a list of dicts with keys:
          name, artist, feed_url, genre, episode_count, url
        """
        url = f"{_ITUNES}?media=podcast&limit={limit}&term={urllib.parse.quote(query)}"
        data = _get_json(url)
        results = []
        for r in (data.get("results") or [])[:limit]:
            results.append(
                {
                    "name": r.get("collectionName") or r.get("trackName", ""),
                    "artist": r.get("artistName", ""),
                    "feed_url": r.get("feedUrl", ""),
                    "genre": r.get("primaryGenreName", ""),
                    "episode_count": r.get("trackCount", 0),
                    "url": r.get("collectionViewUrl") or r.get("trackViewUrl", ""),
                }
            )
        return results

    def transcribe(self, url: str, provider: str = "auto") -> str:
        """Transcribe an episode URL to text via the shared Whisper pipeline."""
        from agent_surf.transcribe import transcribe as _transcribe

        return _transcribe(url, provider=provider)
