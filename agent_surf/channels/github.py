# -*- coding: utf-8 -*-
"""GitHub — check if gh CLI is available."""

from agent_surf.probe import probe_command

from .base import Channel


class GitHubChannel(Channel):
    name = "github"
    description = "GitHub repos and code"
    backends = ["gh CLI"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        return "github.com" in urlparse(url).netloc.lower()

    def check(self, config=None):
        # 真跑 gh auth status 探活。注意：未登录时 rc!=0 是正常业务态（warn），不是 error。
        probe = probe_command("gh", ["auth", "status"], timeout=10, package="gh")
        if probe.status == "missing":
            self.active_backend = None
            return "warn", "gh CLI not installed. Install: https://cli.github.com"
        if probe.status == "broken":
            # gh 是二进制安装（brew/官方包），不是 pip 包——处方不用 pipx/uv 文案
            self.active_backend = None
            return "error", (
                "gh command exists but cannot execute — installation is broken. Reinstall to fix:\n"
                "  brew reinstall gh\n"
                "Or reinstall gh CLI from https://cli.github.com"
            )
        if probe.status == "timeout":
            # gh 本体能启动（工具是活的），只是状态检查超时
            self.active_backend = "gh CLI"
            return "warn", "gh CLI status check timed out. Run gh auth status for details"
        if probe.ok:
            self.active_backend = "gh CLI"
            return "ok", "Fully available (read, search, fork, issues, PRs, etc.)"
        # rc != 0：gh 活着但未认证（gh auth status 的正常业务态）
        self.active_backend = "gh CLI"
        return "warn", "gh CLI installed but not authenticated. Run gh auth login to unlock full features"
