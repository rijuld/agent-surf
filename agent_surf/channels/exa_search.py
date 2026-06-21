# -*- coding: utf-8 -*-
"""Exa Search — check if mcporter + Exa MCP is available."""

from agent_surf.probe import probe_command

from .base import Channel

#: mcporter 是 npm 包，断链处方与默认的 pipx/uv 不同
_MCPORTER_BROKEN_HINT = "mcporter cannot execute (node environment broken). Reinstall:\n  npm install -g mcporter"


class ExaSearchChannel(Channel):
    name = "exa_search"
    description = "Web-wide semantic search"
    backends = ["Exa via mcporter"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        return False  # Search-only channel

    def check(self, config=None):
        self.active_backend = None
        probe = probe_command("mcporter", ["config", "list"], timeout=10, package="mcporter")
        if probe.status == "missing":
            return "off", (
                "Requires mcporter + Exa MCP. Install:\n"
                "  npm install -g mcporter\n"
                "  mcporter config add exa https://mcp.exa.ai/mcp"
            )
        if probe.status == "broken":
            return "error", _MCPORTER_BROKEN_HINT
        if not probe.ok:  # timeout / error
            return "error", f"mcporter execution error: {probe.hint or probe.output or probe.status}"
        if "exa" in probe.output.lower():
            self.active_backend = self.backends[0]
            return "ok", "Web-wide semantic search available (free, no API key required)"
        return "off", (
            "mcporter installed but Exa not configured. Run:\n"
            "  mcporter config add exa https://mcp.exa.ai/mcp"
        )
