# -*- coding: utf-8 -*-
"""Tests for channel registry basics and health checks."""

import json
import shutil
import subprocess
from urllib.error import URLError

from agent_surf.channels import get_all_channels, get_channel
from agent_surf.channels.hackernews import HackerNewsChannel
from agent_surf.channels.podcasts import PodcastsChannel
from agent_surf.channels.producthunt import ProductHuntChannel
from agent_surf.channels.stocktwits import StockTwitsChannel


class TestChannelRegistry:
    def test_get_channel_by_name(self):
        ch = get_channel("github")
        assert ch is not None
        assert ch.name == "github"

    def test_get_unknown_channel_returns_none(self):
        assert get_channel("not-exists") is None

    def test_all_channels_registered(self):
        channels = get_all_channels()
        names = [ch.name for ch in channels]
        assert "web" in names
        assert "github" in names
        assert "twitter" in names
        assert "hackernews" in names


class TestRedditChannel:
    """多后端：OpenCLI > rdt-cli，没有零配置路径。"""

    @staticmethod
    def _isolate(monkeypatch, opencli=None):
        """隔离 OpenCLI 候选（None = 未安装），聚焦 rdt-cli 路径。"""
        from agent_surf.channels.reddit import RedditChannel
        monkeypatch.setattr(RedditChannel, "_check_opencli", lambda self: opencli)

    def test_reports_off_when_nothing_installed(self, monkeypatch):
        self._isolate(monkeypatch)
        monkeypatch.setattr(shutil, "which", lambda _: None)
        from agent_surf.channels.reddit import RedditChannel
        status, msg = RedditChannel().check()
        assert status == "off"
        # 诚实口径：明说没有零配置路径，推荐 OpenCLI + rdt git 源
        assert "zero-config" in msg
        assert "opencli" in msg
        assert "git+https://github.com/public-clis/rdt-cli.git" in msg

    def test_opencli_ready_wins(self, monkeypatch):
        self._isolate(monkeypatch, opencli=("ok", "OpenCLI available (reuses browser login)"))
        monkeypatch.setattr(shutil, "which", lambda _: None)
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert ch.active_backend == "OpenCLI"

    def test_reports_ok_when_authenticated(self, monkeypatch):
        self._isolate(monkeypatch)
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/rdt")
        fake_output = json.dumps({
            "ok": True,
            "schema_version": "1",
            "data": {"authenticated": True, "username": "testuser", "cookie_count": 1},
        })

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, fake_output, "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert "testuser" in msg
        assert ch.active_backend == "rdt-cli"

    def test_reports_warn_when_not_authenticated(self, monkeypatch):
        self._isolate(monkeypatch)
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/rdt")
        fake_output = json.dumps({
            "ok": True,
            "schema_version": "1",
            "data": {"authenticated": False, "username": None, "cookie_count": 0},
        })

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, fake_output, "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        status, msg = ch.check()
        assert status == "warn"
        assert "403" in msg
        assert "rdt login" in msg
        assert "Cookie-Editor" in msg
        assert "chromewebstore.google.com" in msg
        # 未登录是业务态：进程活着，后端仍然算可用
        assert ch.active_backend == "rdt-cli"

    def test_reports_error_when_status_check_fails(self, monkeypatch):
        """rdt 非零退出且输出不可解析 → 工具异常（error），不再算 warn。"""
        self._isolate(monkeypatch)
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/rdt")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, "not valid json{{{", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "rdt exited abnormally" in msg
        assert ch.active_backend is None

    def test_reports_error_with_reinstall_hint_when_broken(self, monkeypatch):
        """which 命中但 exec 抛 FileNotFoundError（venv 断链）→ error + 重装处方。"""
        self._isolate(monkeypatch)
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/rdt")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError("/usr/local/bin/rdt")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "cannot execute" in msg
        assert "pipx install --force" in msg  # rdt 专用 git 源重装处方
        assert "git+https://github.com/public-clis/rdt-cli.git" in msg
        assert ch.active_backend is None

    def test_reports_error_with_reinstall_hint_on_exit_127(self, monkeypatch):
        """退出码 127（找到但跑不动）同样按断链处理。"""
        self._isolate(monkeypatch)
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/rdt")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 127, "", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "pipx install --force" in msg
        assert ch.active_backend is None

    def test_can_handle_reddit_urls(self):
        from agent_surf.channels.reddit import RedditChannel
        ch = RedditChannel()
        assert ch.can_handle("https://www.reddit.com/r/python/comments/abc123/")
        assert ch.can_handle("https://redd.it/abc123")
        assert not ch.can_handle("https://github.com/user/repo")
        assert not ch.can_handle("https://news.ycombinator.com/item?id=123")


class TestYouTubeChannel:
    def test_reports_error_with_reinstall_hint_when_broken(self, monkeypatch):
        """yt-dlp which 命中但 exec 抛 FileNotFoundError → error + 重装处方。"""
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/yt-dlp")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError(cmd[0])

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.youtube import YouTubeChannel
        ch = YouTubeChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "cannot execute" in msg
        assert "uv tool install --force yt-dlp" in msg
        assert ch.active_backend is None


class TestGitHubChannel:
    def test_reports_error_with_reinstall_hint_when_broken(self, monkeypatch):
        """gh which 命中但 exec 失败 → error + brew 重装处方（gh 不是 pip 包）。"""
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/gh")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError(cmd[0])

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.github import GitHubChannel
        ch = GitHubChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "cannot execute" in msg
        assert "brew reinstall gh" in msg
        assert ch.active_backend is None

    def test_active_backend_set_when_authenticated(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/gh")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "Logged in to github.com", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.github import GitHubChannel
        ch = GitHubChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert ch.active_backend == "gh CLI"

    def test_active_backend_set_when_unauthenticated(self, monkeypatch):
        """gh auth status 非零退出是正常业务态（未登录）：warn 但后端可用。"""
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/gh")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, "", "You are not logged in")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.github import GitHubChannel
        ch = GitHubChannel()
        status, msg = ch.check()
        assert status == "warn"
        assert "gh auth login" in msg
        assert ch.active_backend == "gh CLI"


class TestLinkedInChannel:
    def test_reports_error_with_reinstall_hint_when_broken(self, monkeypatch):
        """mcporter which 命中但 exec 失败 → error + npm 重装处方。"""
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/mcporter")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError(cmd[0])

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.linkedin import LinkedInChannel
        ch = LinkedInChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "npm install -g mcporter" in msg
        assert ch.active_backend is None

    def test_active_backend_set_when_linkedin_configured(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/mcporter")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "linkedin  http://localhost:3000/mcp", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.linkedin import LinkedInChannel
        ch = LinkedInChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert ch.active_backend == "linkedin-scraper-mcp"

    def test_off_without_backend_when_linkedin_not_configured(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/mcporter")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "exa  https://mcp.exa.ai/mcp", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.linkedin import LinkedInChannel
        ch = LinkedInChannel()
        status, msg = ch.check()
        assert status == "off"
        assert ch.active_backend is None


class TestExaSearchChannel:
    def test_reports_error_with_reinstall_hint_when_broken(self, monkeypatch):
        """mcporter which 命中但 exec 失败 → error + npm 重装处方。"""
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/mcporter")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError(cmd[0])

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.exa_search import ExaSearchChannel
        ch = ExaSearchChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "npm install -g mcporter" in msg
        assert ch.active_backend is None

    def test_active_backend_set_when_exa_configured(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/mcporter")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "exa  https://mcp.exa.ai/mcp", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        from agent_surf.channels.exa_search import ExaSearchChannel
        ch = ExaSearchChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert ch.active_backend == "Exa via mcporter"


def _fake_urlopen(payload):
    """Return a urlopen replacement that yields *payload* (bytes or JSON-able)."""
    body = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode()

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self):
            return body

    return lambda req, timeout=None: FakeResponse()


class TestHackerNewsChannel:
    def test_can_handle_hn_urls(self):
        ch = HackerNewsChannel()
        assert ch.can_handle("https://news.ycombinator.com/item?id=123")
        assert ch.can_handle("https://hn.algolia.com/api/v1/search?query=x")
        assert not ch.can_handle("https://github.com/user/repo")
        assert not ch.can_handle("https://reddit.com/r/python")

    def test_check_ok_when_api_reachable(self, monkeypatch):
        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(b"[1,2,3]"))
        status, msg = HackerNewsChannel().check()
        assert status == "ok"
        assert "Public API available" in msg

    def test_check_warn_when_api_unreachable(self, monkeypatch):
        import urllib.request

        def raise_error(req, timeout=None):
            raise URLError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", raise_error)
        status, msg = HackerNewsChannel().check()
        assert status == "warn"
        assert "failed" in msg

    def test_get_top_stories_returns_list(self, monkeypatch):
        import urllib.request

        fake = {"hits": [
            {"objectID": "111", "title": "Show HN: Foo", "url": "https://foo.dev",
             "author": "alice", "points": 42, "num_comments": 10, "created_at": "2026-01-01T00:00:00Z"},
            {"objectID": "222", "title": "Ask HN: Bar", "url": None,
             "author": "bob", "points": 5, "num_comments": 2, "created_at": "2026-01-02T00:00:00Z"},
        ]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        stories = HackerNewsChannel().get_top_stories(limit=5)
        assert len(stories) == 2
        assert stories[0]["id"] == 111
        assert stories[0]["title"] == "Show HN: Foo"
        assert stories[0]["points"] == 42
        # Missing url falls back to the HN item permalink.
        assert stories[1]["url"] == "https://news.ycombinator.com/item?id=222"

    def test_search_returns_results(self, monkeypatch):
        import urllib.request

        fake = {"hits": [
            {"objectID": "900", "title": "Rust async", "url": "https://r.dev",
             "author": "carol", "points": 100, "num_comments": 30, "created_at": "2026-03-01T00:00:00Z"},
        ]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        results = HackerNewsChannel().search("rust", limit=10)
        assert len(results) == 1
        assert results[0]["id"] == 900
        assert results[0]["author"] == "carol"

    def test_get_item_returns_detail_and_comments(self, monkeypatch):
        import urllib.request

        fake = {
            "id": 999, "title": "Big launch", "url": "https://big.dev", "text": "",
            "author": "dave", "points": 300, "created_at": "2026-04-01T00:00:00Z",
            "children": [
                {"id": 1000, "author": "eve", "text": "Nice", "created_at": "x", "children": [
                    {"id": 1001, "author": "frank", "text": "Agreed", "created_at": "y", "children": []},
                ]},
            ],
        }
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        item = HackerNewsChannel().get_item(999)
        assert item["id"] == 999
        assert item["author"] == "dave"
        assert len(item["children"]) == 1
        assert item["children"][0]["author"] == "eve"
        assert item["children"][0]["children"][0]["text"] == "Agreed"

    def test_get_user_returns_profile(self, monkeypatch):
        import urllib.request

        fake = {"id": "alice", "karma": 5000, "about": "hacker",
                "created": 1500000000, "submitted": [1, 2, 3]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        user = HackerNewsChannel().get_user("alice")
        assert user["id"] == "alice"
        assert user["karma"] == 5000
        assert user["submitted_count"] == 3
        assert "alice" in user["url"]


class TestStockTwitsChannel:
    def test_can_handle_urls(self):
        ch = StockTwitsChannel()
        assert ch.can_handle("https://stocktwits.com/symbol/AAPL")
        assert ch.can_handle("https://finance.yahoo.com/quote/MSFT")
        assert not ch.can_handle("https://github.com/user/repo")

    def test_check_ok_when_api_reachable(self, monkeypatch):
        import urllib.request

        monkeypatch.setattr(
            urllib.request, "urlopen",
            _fake_urlopen({"response": {"status": 200}, "symbols": []}),
        )
        status, msg = StockTwitsChannel().check()
        assert status == "ok"
        assert "Public API available" in msg

    def test_check_warn_when_api_unreachable(self, monkeypatch):
        import urllib.request

        def raise_error(req, timeout=None):
            raise URLError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", raise_error)
        status, msg = StockTwitsChannel().check()
        assert status == "warn"
        assert "failed" in msg

    def test_get_stock_quote_parses_yahoo(self, monkeypatch):
        import urllib.request

        fake = {"chart": {"result": [{
            "meta": {"symbol": "AAPL", "shortName": "Apple Inc.",
                     "regularMarketPrice": 190.0, "chartPreviousClose": 188.0,
                     "currency": "USD", "regularMarketTime": 1700000000},
            "indicators": {"quote": [{"open": [187.5], "high": [191.0],
                                      "low": [186.0], "volume": [12345678]}]},
        }]}}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        q = StockTwitsChannel().get_stock_quote("AAPL")
        assert q["symbol"] == "AAPL"
        assert q["current"] == 190.0
        assert q["last_close"] == 188.0
        assert q["chg"] == 2.0
        assert round(q["percent"], 2) == round(2.0 / 188.0 * 100, 2)
        assert q["high"] == 191.0
        assert q["open"] == 187.5
        assert q["volume"] == 12345678

    def test_search_symbols(self, monkeypatch):
        import urllib.request

        fake = {"results": [
            {"symbol": "AAPL", "title": "Apple Inc.", "exchange": "NASDAQ"},
            {"symbol": "AAPL.MX", "title": "Apple", "exchange": "BMV"},
        ]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        results = StockTwitsChannel().search_symbols("apple", limit=5)
        assert len(results) == 2
        assert results[0]["symbol"] == "AAPL"
        assert results[0]["exchange"] == "NASDAQ"

    def test_get_trending_symbols_ranks(self, monkeypatch):
        import urllib.request

        fake = {"response": {"status": 200}, "symbols": [
            {"symbol": "TSLA", "title": "Tesla", "watchlist_count": 500000},
            {"symbol": "NVDA", "title": "NVIDIA", "watchlist_count": 400000},
        ]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        results = StockTwitsChannel().get_trending_symbols(limit=10)
        assert len(results) == 2
        assert results[0]["symbol"] == "TSLA"
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 2

    def test_get_symbol_stream(self, monkeypatch):
        import urllib.request

        fake = {"messages": [
            {"id": 1, "body": "to the moon", "user": {"username": "trader1"},
             "likes": {"total": 7}, "created_at": "2026-01-01T00:00:00Z"},
        ]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        msgs = StockTwitsChannel().get_symbol_stream("TSLA", limit=10)
        assert len(msgs) == 1
        assert msgs[0]["author"] == "trader1"
        assert msgs[0]["likes"] == 7


class TestPodcastsChannel:
    def test_can_handle_urls(self):
        ch = PodcastsChannel()
        assert ch.can_handle("https://podcasts.apple.com/us/podcast/x/id123")
        assert not ch.can_handle("https://github.com/user/repo")

    def test_reports_error_when_ffmpeg_broken(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/ffmpeg")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError(cmd[0])

        monkeypatch.setattr(subprocess, "run", fake_run)
        ch = PodcastsChannel()
        status, msg = ch.check()
        assert status == "error"
        assert "cannot execute" in msg
        assert "brew install ffmpeg" in msg
        assert ch.active_backend is None

    def test_active_backend_set_when_fully_configured(self, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/tool")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "version 1.0", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
        ch = PodcastsChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert ch.active_backend == "groq-whisper"

    def test_warn_when_no_provider_key(self, monkeypatch, tmp_path):
        from agent_surf.config import Config

        monkeypatch.setattr(shutil, "which", lambda _: "/usr/local/bin/tool")

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "version 1.0", "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        cfg = Config(config_path=tmp_path / "config.yaml")
        ch = PodcastsChannel()
        status, msg = ch.check(cfg)
        assert status == "warn"
        assert "Groq API key" in msg
        assert ch.active_backend is None

    def test_search_returns_list(self, monkeypatch):
        import urllib.request

        fake = {"results": [
            {"collectionName": "The Daily", "artistName": "NYT", "feedUrl": "https://feed",
             "primaryGenreName": "News", "trackCount": 1500, "collectionViewUrl": "https://pod"},
        ]}
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(fake))
        results = PodcastsChannel().search("news", limit=5)
        assert len(results) == 1
        assert results[0]["name"] == "The Daily"
        assert results[0]["artist"] == "NYT"


class TestProductHuntChannel:
    def test_can_handle_urls(self):
        ch = ProductHuntChannel()
        assert ch.can_handle("https://www.producthunt.com/posts/some-tool")
        assert not ch.can_handle("https://github.com/user/repo")

    def test_check_warn_without_token(self, monkeypatch):
        import agent_surf.channels.producthunt as ph

        monkeypatch.setattr(ph, "_token", lambda config=None: None)
        ch = ProductHuntChannel()
        status, msg = ch.check()
        assert status == "warn"
        assert "token required" in msg.lower()
        assert ch.active_backend is None

    def test_check_ok_with_valid_token(self, monkeypatch):
        import agent_surf.channels.producthunt as ph

        monkeypatch.setattr(ph, "_token", lambda config=None: "tok")
        monkeypatch.setattr(
            ph, "_graphql",
            lambda q, t, v=None: {"data": {"viewer": {"user": {"username": "alice"}}}},
        )
        ch = ProductHuntChannel()
        status, msg = ch.check()
        assert status == "ok"
        assert ch.active_backend == "Product Hunt API (token)"

    def test_check_warn_when_token_rejected(self, monkeypatch):
        import agent_surf.channels.producthunt as ph

        monkeypatch.setattr(ph, "_token", lambda config=None: "bad")
        monkeypatch.setattr(
            ph, "_graphql",
            lambda q, t, v=None: {"errors": [{"message": "Unauthorized"}]},
        )
        ch = ProductHuntChannel()
        status, msg = ch.check()
        assert status == "warn"
        assert "rejected" in msg.lower()
        assert ch.active_backend is None

    def test_get_trending_returns_list(self, monkeypatch):
        import agent_surf.channels.producthunt as ph

        monkeypatch.setattr(ph, "_token", lambda config=None: "tok")
        payload = {"data": {"posts": {"edges": [
            {"node": {"id": "1", "name": "Tool A", "tagline": "Does A", "votesCount": 120,
                      "commentsCount": 8, "url": "https://ph/a",
                      "topics": {"edges": [{"node": {"name": "AI"}}]}}},
        ]}}}
        monkeypatch.setattr(ph, "_graphql", lambda q, t, v=None: payload)
        results = ProductHuntChannel().get_trending(limit=10)
        assert len(results) == 1
        assert results[0]["name"] == "Tool A"
        assert results[0]["votes"] == 120
        assert results[0]["topics"] == ["AI"]

    def test_search_filters_by_query(self, monkeypatch):
        import agent_surf.channels.producthunt as ph

        monkeypatch.setattr(ph, "_token", lambda config=None: "tok")
        payload = {"data": {"posts": {"edges": [
            {"node": {"id": "1", "name": "Notion AI", "tagline": "notes", "votesCount": 50,
                      "commentsCount": 3, "url": "https://ph/1", "topics": {"edges": []}}},
            {"node": {"id": "2", "name": "Figma", "tagline": "design", "votesCount": 90,
                      "commentsCount": 5, "url": "https://ph/2", "topics": {"edges": []}}},
        ]}}}
        monkeypatch.setattr(ph, "_graphql", lambda q, t, v=None: payload)
        results = ProductHuntChannel().search("notion", limit=10)
        assert len(results) == 1
        assert results[0]["name"] == "Notion AI"

    def test_get_trending_without_token_returns_error(self, monkeypatch):
        import agent_surf.channels.producthunt as ph

        monkeypatch.setattr(ph, "_token", lambda config=None: None)
        results = ProductHuntChannel().get_trending(limit=5)
        assert len(results) == 1
        assert "error" in results[0]
