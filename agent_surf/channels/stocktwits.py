# -*- coding: utf-8 -*-
"""StockTwits + Yahoo Finance — US stock quotes and investing community.

Quotes come from Yahoo Finance's public chart API (no key, reliable OHLC/volume).
Symbol search, community streams, and trending symbols come from the public
StockTwits API. StockTwits has tightened access over time, so check() probes it
live and degrades to `warn` honestly when blocked — Yahoo Finance quotes remain
the reliable core either way.
"""

import json
import urllib.parse
import urllib.request
from typing import Any

from .base import Channel

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_TIMEOUT = 10
_STOCKTWITS = "https://api.stocktwits.com/api/2"
_YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"


def _get_json(url: str) -> Any:
    """Fetch *url* and return parsed JSON. Raises on HTTP/network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _last(arr) -> Any:
    """Last non-null value of a Yahoo indicator array (or None)."""
    vals = [v for v in (arr or []) if v is not None]
    return vals[-1] if vals else None


class StockTwitsChannel(Channel):
    name = "stocktwits"
    description = "StockTwits quotes and investing community"
    backends = ["StockTwits + Yahoo Finance (public)"]
    tier = 1

    # ------------------------------------------------------------------ #
    # URL routing
    # ------------------------------------------------------------------ #

    def can_handle(self, url: str) -> bool:
        d = urllib.parse.urlparse(url).netloc.lower()
        return "stocktwits.com" in d or "finance.yahoo.com" in d

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #

    def check(self, config=None):
        self.active_backend = None
        try:
            data = _get_json(f"{_STOCKTWITS}/trending/symbols.json")
            if (data.get("response") or {}).get("status") == 200:
                self.active_backend = self.backends[0]
                return "ok", (
                    "Public API available (quotes via Yahoo Finance, community "
                    "streams, symbol search, trending stocks)"
                )
            return "warn", (
                "StockTwits API response abnormal (community streams may be "
                "rate-limited; Yahoo Finance quotes still work)"
            )
        except Exception as e:
            return "warn", (
                f"StockTwits API connection failed: {e}. "
                "Yahoo Finance quotes still work; community streams may be rate-limited or blocked."
            )

    # ------------------------------------------------------------------ #
    # Quotes (Yahoo Finance)
    # ------------------------------------------------------------------ #

    def get_stock_quote(self, symbol: str) -> dict:
        """Real-time quote via Yahoo Finance.

        Args:
            symbol: US ticker like AAPL, MSFT, or an index like ^GSPC (S&P 500)

        Returns a dict with keys:
          symbol, name, current, chg, percent, high, low, open, last_close,
          volume, market_capital, currency, timestamp
        """
        data = _get_json(
            f"{_YAHOO_CHART}/{urllib.parse.quote(symbol)}?interval=1d&range=1d"
        )
        result = ((data.get("chart") or {}).get("result") or [{}])[0] or {}
        meta = result.get("meta") or {}
        quote = ((result.get("indicators") or {}).get("quote") or [{}])[0] or {}

        current = meta.get("regularMarketPrice")
        last_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        chg = (current - last_close) if (current is not None and last_close) else None
        percent = (chg / last_close * 100) if (chg is not None and last_close) else None

        return {
            "symbol": meta.get("symbol", symbol),
            "name": meta.get("longName") or meta.get("shortName", ""),
            "current": current,
            "chg": round(chg, 4) if chg is not None else None,
            "percent": round(percent, 4) if percent is not None else None,
            "high": meta.get("regularMarketDayHigh") or _last(quote.get("high")),
            "low": meta.get("regularMarketDayLow") or _last(quote.get("low")),
            "open": _last(quote.get("open")),
            "last_close": last_close,
            "volume": meta.get("regularMarketVolume") or _last(quote.get("volume")),
            "market_capital": meta.get("marketCap"),
            "currency": meta.get("currency", ""),
            "timestamp": meta.get("regularMarketTime"),
        }

    # ------------------------------------------------------------------ #
    # Community + discovery (StockTwits)
    # ------------------------------------------------------------------ #

    def search_symbols(self, query: str, limit: int = 10) -> list:
        """Search tickers by name or symbol.

        Returns a list of dicts with keys: symbol, name, exchange
        """
        data = _get_json(
            f"{_STOCKTWITS}/search/symbols.json?q={urllib.parse.quote(query)}"
        )
        results = []
        for s in (data.get("results") or [])[:limit]:
            results.append(
                {
                    "symbol": s.get("symbol", ""),
                    "name": s.get("title", ""),
                    "exchange": s.get("exchange", ""),
                }
            )
        return results

    def get_symbol_stream(self, symbol: str, limit: int = 20) -> list:
        """Recent community messages for a symbol.

        Returns a list of dicts with keys:
          id, body, author, likes, created_at
        """
        data = _get_json(
            f"{_STOCKTWITS}/streams/symbol/{urllib.parse.quote(symbol)}.json"
        )
        results = []
        for m in (data.get("messages") or [])[:limit]:
            user = m.get("user") or {}
            results.append(
                {
                    "id": m.get("id", 0),
                    "body": m.get("body", "") or "",
                    "author": user.get("username", ""),
                    "likes": (m.get("likes") or {}).get("total", 0),
                    "created_at": m.get("created_at", ""),
                }
            )
        return results

    def get_trending_symbols(self, limit: int = 10) -> list:
        """Trending tickers on StockTwits.

        Returns a list of dicts with keys:
          symbol, name, watchlist_count, rank
        """
        data = _get_json(f"{_STOCKTWITS}/trending/symbols.json?limit={limit}")
        results = []
        for idx, s in enumerate((data.get("symbols") or [])[:limit], 1):
            results.append(
                {
                    "symbol": s.get("symbol", ""),
                    "name": s.get("title", ""),
                    "watchlist_count": s.get("watchlist_count", 0),
                    "rank": idx,
                }
            )
        return results
