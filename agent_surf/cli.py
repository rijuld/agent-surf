# -*- coding: utf-8 -*-
"""
Agent Surf CLI — installer, doctor, and configuration tool.

Usage:
    agent-surf install --env=auto
    agent-surf doctor
    agent-surf configure twitter-cookies "auth_token=xxx; ct0=yyy"
    agent-surf setup
"""

import sys
import argparse
import json
import os
import time

from agent_surf import __version__

# Pinned to the 0.4.2 state — PyPI still only has 0.4.1 (upstream issue #10).
_RDT_GIT_SOURCE = "git+https://github.com/public-clis/rdt-cli.git@5e4fb3720d5c174e976cd425ccc3b879d52cac66"


def _ensure_utf8_console():
    """Best-effort Windows console UTF-8 setup for CLI runtime only."""
    if sys.platform != "win32":
        return
    # Avoid interfering with pytest/captured streams.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    try:
        import io
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        # Do not crash CLI just because encoding patch failed.
        pass


def _configure_logging(verbose: bool = False):
    """Suppress loguru output unless --verbose is set."""
    from loguru import logger
    logger.remove()  # Remove default stderr handler
    if verbose:
        logger.add(sys.stderr, level="INFO")


def main():
    _ensure_utf8_console()

    parser = argparse.ArgumentParser(
        prog="agent-surf",
        description="Give your AI Agent eyes to see the entire internet",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug logs")
    parser.add_argument("--version", action="version", version=f"Agent Surf v{__version__}")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── setup ──
    sub.add_parser("setup", help="Interactive configuration wizard")

    # ── install ──
    p_install = sub.add_parser("install", help="One-shot installer with flags")
    p_install.add_argument("--env", choices=["local", "server", "auto"], default="auto",
                           help="Environment: local, server, or auto-detect")
    p_install.add_argument("--proxy", default="",
                           help="Network proxy saved for agents to export as HTTP(S)_PROXY "
                                "in restricted networks (http://user:pass@ip:port)")
    p_install.add_argument("--safe", action="store_true",
                           help="Safe mode: skip automatic system changes, show what's needed instead")
    p_install.add_argument("--dry-run", action="store_true",
                           help="Show what would be done without making any changes")
    p_install.add_argument("--channels", default="",
                           help="Comma-separated optional channels to install "
                                "(twitter,podcasts,reddit,opencli,linkedin,all)")

    # ── configure ──
    p_conf = sub.add_parser("configure", help="Set a config value or auto-extract from browser")
    p_conf.add_argument("key", nargs="?", default=None,
                        choices=["proxy", "github-token", "groq-key", "openai-key",
                                 "twitter-cookies", "youtube-cookies",
                                 "producthunt-token"],
                        help="What to configure (omit if using --from-browser)")
    p_conf.add_argument("value", nargs="*", help="The value(s) to set")
    p_conf.add_argument("--from-browser", metavar="BROWSER",
                        choices=["chrome", "firefox", "edge", "brave", "opera"],
                        help="Auto-extract ALL platform cookies from browser (chrome/firefox/edge/brave/opera)")

    # ── doctor ──
    p_doctor = sub.add_parser("doctor", help="Check platform availability")
    p_doctor.add_argument("--json", action="store_true",
                          help="Output machine-readable JSON instead of the text report")

    # ── uninstall ──
    p_uninstall = sub.add_parser("uninstall", help="Remove all Agent Surf config, tokens, and skill files")
    p_uninstall.add_argument("--dry-run", action="store_true",
                             help="Show what would be removed without making any changes")
    p_uninstall.add_argument("--keep-config", action="store_true",
                             help="Remove skill files only, keep ~/.agent-surf/ config and tokens")

    # ── skill ──
    p_skill = sub.add_parser("skill", help="Manage agent skill registration")
    p_skill_group = p_skill.add_mutually_exclusive_group(required=True)
    p_skill_group.add_argument("--install", action="store_true",
                               help="Install SKILL.md to agent skill directories")
    p_skill_group.add_argument("--uninstall", action="store_true",
                               help="Remove SKILL.md from agent skill directories")

    # ── check-update ──
    # ── transcribe ──
    p_tr = sub.add_parser("transcribe", help="Transcribe a URL or local audio file (Whisper via Groq/OpenAI)")
    p_tr.add_argument("source", help="Audio/video URL or local file path")
    p_tr.add_argument("--provider", choices=["auto", "groq", "openai"], default="auto",
                      help="Transcription provider (default: auto = groq → openai fallback)")
    p_tr.add_argument("-o", "--output", default=None,
                      help="Write transcript to a file instead of stdout")

    sub.add_parser("check-update", help="Check for new versions and changes")

    # ── watch ──
    sub.add_parser("watch", help="Quick health check + update check (for scheduled tasks)")

    # ── version ──
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()

    # Suppress loguru noise unless --verbose
    _configure_logging(getattr(args, "verbose", False))

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "version":
        print(f"Agent Surf v{__version__}")
        sys.exit(0)

    if args.command == "doctor":
        _cmd_doctor(args)
    elif args.command == "check-update":
        _cmd_check_update()
    elif args.command == "watch":
        _cmd_watch()
    elif args.command == "setup":
        _cmd_setup()
    elif args.command == "install":
        _cmd_install(args)
    elif args.command == "configure":
        _cmd_configure(args)
    elif args.command == "uninstall":
        _cmd_uninstall(args)
    elif args.command == "skill":
        _cmd_skill(args)
    elif args.command == "transcribe":
        _cmd_transcribe(args)


# ── Command handlers ────────────────────────────────


def _cmd_install(args):
    """One-shot deterministic installer."""
    import os
    from agent_surf.config import Config
    from agent_surf.doctor import check_all, format_report

    safe_mode = args.safe
    dry_run = args.dry_run

    config = Config()
    print()
    print("Agent Surf Installer")
    print("=" * 40)

    # Ensure tools directory exists (for upstream tool repos)
    tools_dir = os.path.expanduser("~/.agent-surf/tools")
    os.makedirs(tools_dir, exist_ok=True)

    if dry_run:
        print("DRY RUN — showing what would be done (no changes)")
        print()
    if safe_mode:
        print("SAFE MODE — skipping automatic system changes")
        print()

    # ── Parse --channels ──
    CHANNEL_INSTALLERS = {
        "twitter":   _install_twitter_deps,
        "podcasts":  _install_podcasts_deps,
        "reddit":    _install_reddit_deps,
        "opencli":   _install_opencli_deps,  # cross-channel backend, desktop only
        # producthunt: developer token only, no install step
        # linkedin: manual setup, no auto-install
    }
    COOKIE_CHANNELS = {"twitter"}

    requested_channels = set()
    if args.channels:
        raw = [c.strip().lower() for c in args.channels.split(",") if c.strip()]
        if "all" in raw:
            requested_channels = set(CHANNEL_INSTALLERS.keys()) | {"producthunt", "linkedin"}
        else:
            requested_channels = set(raw)

    # Auto-detect environment
    env = args.env
    if env == "auto":
        env = _detect_environment()

    if env == "server":
        print(f"Environment: Server/VPS (auto-detected)")
    else:
        print(f"Environment: Local computer (auto-detected)")

    # Apply explicit flags
    if args.proxy:
        if dry_run:
            print(f"[dry-run] Would save network proxy")
        else:
            config.set("proxy", args.proxy)
            print(f"✅ Proxy saved (for Agent use when accessing restricted networks)")

    # ── Install core system dependencies (lightweight, always) ──
    print()
    if dry_run:
        _install_system_deps_dryrun()
    elif safe_mode:
        _install_system_deps_safe()
    else:
        _install_system_deps()

    # ── mcporter (for Exa search) ──
    print()
    if dry_run:
        print("[dry-run] Would install mcporter and configure Exa search")
    elif safe_mode:
        _install_mcporter_safe()
    else:
        _install_mcporter()

    # ── Install optional channels (only if --channels specified) ──
    if requested_channels and not dry_run and not safe_mode:
        print()
        print("Installing optional channels...")
        if env == "server" and "opencli" in requested_channels:
            # OpenCLI rides a real desktop Chrome session — useless headless
            requested_channels.discard("opencli")
            print("  -- OpenCLI requires a desktop environment + Chrome; skipping on server")
        for ch_name in sorted(requested_channels):
            installer = CHANNEL_INSTALLERS.get(ch_name)
            if installer:
                installer()

    if requested_channels and dry_run:
        print()
        print(f"[dry-run] Would install optional channels: {', '.join(sorted(requested_channels))}")

    # ── Auto-import cookies (only if cookie-needing channels are requested) ──
    needs_cookies = bool(requested_channels & COOKIE_CHANNELS)
    if env == "local" and needs_cookies and not safe_mode and not dry_run:
        print()
        print("Importing cookies from browser...")
        print("  (macOS may ask for your login password to access the Keychain — this is normal,")
        print("   it only happens once during install. Enter your password or click 'Allow'.)")
        try:
            from agent_surf.cookie_extract import configure_from_browser
            results = configure_from_browser("chrome", config)
            found = False
            for platform, success, message in results:
                if success:
                    print(f"  ✅ {platform}: {message}")
                    found = True
            if not found:
                results = configure_from_browser("firefox", config)
                for platform, success, message in results:
                    if success:
                        print(f"  ✅ {platform}: {message}")
                        found = True
            if not found:
                print("  -- No cookies found (normal if you haven't logged into these sites)")
        except Exception:
            print("  -- Could not read browser cookies (browser might be open or password was denied)")
    elif env == "local" and needs_cookies and dry_run:
        print()
        print("[dry-run] Would try to import cookies from Chrome/Firefox")

    # Environment-specific advice
    if env == "server":
        print()
        print("Tip: Some platforms block datacenter/server IPs.")
        print("   Reddit requires a logged-in session (rdt-cli + Cookie — see doctor hints); restricted networks may also need a proxy.")
        print("   Save a proxy for Agent use: agent-surf configure proxy http://user:pass@ip:port")
        print("   Cheap option: https://www.webshare.io ($1/month)")

    # Test channels
    if not dry_run:
        print()
        print("Testing channels...")
        results = check_all(config)
        ok = sum(1 for r in results.values() if r["status"] == "ok")
        total = len(results)

        # Final status
        print()
        print(format_report(results))
        print()

        # ── Install agent skill ──
        _install_skill()

        print(f"✅ Installation complete! {ok}/{total} channels active.")

        if not requested_channels:
            # First install — hint about optional channels
            print()
            print("More channels available! Use --channels to install:")
            print("   agent-surf install --channels=twitter,podcasts,reddit,...")
            print("   agent-surf install --channels=all  (install everything)")

        # Star reminder
        print()
        print("If Agent Surf helped you, give it a Star so more people can find it:")
        print("   https://github.com/rijuld/agent-surf")
        print("   Takes one second — it means a lot to an indie developer. Thank you!")
    else:
        print()
        print("Dry run complete. No changes were made.")


def _install_skill():
    """Install Agent Surf as an agent skill (OpenClaw / Claude Code / .agents)."""
    import os
    import shutil
    import importlib.resources

    def _copy_skill_dir(target: str) -> bool:
        """Copy entire skill directory (SKILL.md + references/)."""
        try:
            # Clear existing installation. A symlinked skill dir (dotfiles
            # setups) breaks shutil.rmtree — unlink the link itself instead.
            if os.path.islink(target):
                os.unlink(target)
            elif os.path.exists(target):
                shutil.rmtree(target)
            os.makedirs(target, exist_ok=True)

            # Get skill directory from package (with fallback for editable installs)
            try:
                skill_pkg = importlib.resources.files("agent_surf").joinpath("skill")
                skill_md = skill_pkg.joinpath("SKILL.md").read_text(encoding="utf-8")
            except Exception:
                from pathlib import Path
                skill_pkg = Path(__file__).resolve().parent / "skill"
                skill_md = skill_pkg.joinpath("SKILL.md").read_text(encoding="utf-8")

            # Copy SKILL.md
            with open(os.path.join(target, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_md)

            # Copy references/ directory
            refs_pkg = skill_pkg.joinpath("references")
            refs_target = os.path.join(target, "references")
            os.makedirs(refs_target, exist_ok=True)

            for ref_file in refs_pkg.iterdir():
                name = ref_file.name if hasattr(ref_file, 'name') else str(ref_file).split('/')[-1]
                if name.endswith(".md"):
                    content = ref_file.read_text(encoding="utf-8") if hasattr(ref_file, 'read_text') else ref_file.read_text()
                    with open(os.path.join(refs_target, name), "w", encoding="utf-8") as f:
                        f.write(content)

            return True
        except Exception as e:
            print(f"  Warning: Could not install skill: {e}")
            return False

    # Determine skill install path (priority: .agents > openclaw > claude)
    skill_dirs = [
        os.path.expanduser("~/.agents/skills"),      # Generic agents (priority)
        os.path.expanduser("~/.openclaw/skills"),    # OpenClaw
        os.path.expanduser("~/.claude/skills"),      # Claude Code (if exists)
    ]

    # Insert OPENCLAW_HOME path at the beginning if environment variable is set
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        skill_dirs.insert(0, os.path.join(openclaw_home, ".openclaw", "skills"))

    installed = False
    for skill_dir in skill_dirs:
        if os.path.isdir(skill_dir):
            target = os.path.join(skill_dir, "agent-surf")
            if _copy_skill_dir(target):
                platform_name = "Agent" if ".agents" in skill_dir else "OpenClaw" if "openclaw" in skill_dir else "Claude Code"
                print(f"Skill installed for {platform_name}: {target}")
                installed = True

    if not installed:
        # No known skill directory found — create for .agents by default
        target = os.path.expanduser("~/.agents/skills/agent-surf")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if _copy_skill_dir(target):
            print(f"Skill installed: {target}")
        else:
            print("  -- Could not install agent skill (optional)")
            print("  -- Tip: install OpenClaw, Claude Code, or create ~/.agents/skills/ manually")


def _uninstall_skill():
    """Remove SKILL.md from all known agent skill directories."""
    import shutil

    skill_dirs = [
        ("~/.openclaw/skills/agent-surf", "OpenClaw"),
        ("~/.claude/skills/agent-surf", "Claude Code"),
        ("~/.agents/skills/agent-surf", "Agent"),
    ]

    # Also check OPENCLAW_HOME
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        skill_dirs.insert(
            0,
            (os.path.join(openclaw_home, ".openclaw", "skills", "agent-surf"), "OpenClaw"),
        )

    removed = False
    for skill_path_template, platform_name in skill_dirs:
        skill_path = os.path.expanduser(skill_path_template)
        if os.path.isdir(skill_path):
            try:
                if os.path.islink(skill_path):
                    os.unlink(skill_path)
                else:
                    shutil.rmtree(skill_path)
                print(f"  Removed {platform_name} skill: {skill_path}")
                removed = True
            except Exception as e:
                print(f"  Could not remove {skill_path}: {e}")

    if not removed:
        print("  No skill installations found.")


def _cmd_skill(args):
    """Manage agent skill registration."""
    if args.install:
        _install_skill()
    elif args.uninstall:
        _uninstall_skill()


def _install_system_deps():
    """Install system-level dependencies: gh CLI, Node.js (for mcporter)."""
    import shutil
    import subprocess
    import platform
    import tempfile

    print("Checking system dependencies...")

    # ── gh CLI ──
    if shutil.which("gh"):
        print("  ✅ gh CLI already installed")
    else:
        print("  Installing gh CLI...")
        os_type = platform.system().lower()
        if os_type == "linux":
            try:
                # Official GitHub apt source setup without invoking a shell.
                keyring_path = "/usr/share/keyrings/githubcli-archive-keyring.gpg"
                list_path = "/etc/apt/sources.list.d/github-cli.list"
                arch = subprocess.run(
                    ["dpkg", "--print-architecture"],
                    capture_output=True, encoding="utf-8", errors="replace", timeout=10,
                ).stdout.strip() or "amd64"
                subprocess.run(
                    ["curl", "-fsSL", "https://cli.github.com/packages/githubcli-archive-keyring.gpg", "-o", keyring_path],
                    capture_output=True, timeout=60,
                )
                repo_line = (
                    f"deb [arch={arch} signed-by={keyring_path}] "
                    "https://cli.github.com/packages stable main\n"
                )
                with open(list_path, "w", encoding="utf-8") as f:
                    f.write(repo_line)
                subprocess.run(["apt-get", "update", "-qq"], capture_output=True, timeout=60)
                subprocess.run(["apt-get", "install", "-y", "-qq", "gh"], capture_output=True, timeout=60)
                if shutil.which("gh"):
                    print("  ✅ gh CLI installed")
                else:
                    print("  [!]  gh CLI install failed. You can try: snap install gh, or download from https://github.com/cli/cli/releases")
            except Exception:
                print("  [!]  gh CLI install failed. You can try: snap install gh, or download from https://github.com/cli/cli/releases")
        elif os_type == "darwin":
            if shutil.which("brew"):
                try:
                    subprocess.run(["brew", "install", "gh"], capture_output=True, timeout=120)
                    if shutil.which("gh"):
                        print("  ✅ gh CLI installed")
                    else:
                        print("  [!]  gh CLI install failed. Try: brew install gh")
                except Exception:
                    print("  [!]  gh CLI install failed. Try: brew install gh")
            else:
                print("  [!]  gh CLI not found. Install: https://cli.github.com")
        else:
            print("  [!]  gh CLI not found. Install: https://cli.github.com")

    # ── Node.js (needed for mcporter) ──
    if shutil.which("node") and shutil.which("npm"):
        print("  ✅ Node.js already installed")
    else:
        print("  Installing Node.js...")
        try:
            # Use NodeSource setup script without invoking a shell pipeline.
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sh") as tf:
                script_path = tf.name
            subprocess.run(
                ["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", script_path],
                capture_output=True, timeout=60,
            )
            subprocess.run(
                ["bash", script_path],
                capture_output=True, timeout=120,
            )
            try:
                os.unlink(script_path)
            except Exception:
                pass
            subprocess.run(
                ["apt-get", "install", "-y", "-qq", "nodejs"],
                capture_output=True, timeout=120,
            )
            if shutil.which("node"):
                print("  ✅ Node.js installed")
            else:
                print("  [!]  Node.js install failed. Try: apt install nodejs npm, or nvm install 22, or download from https://nodejs.org")
        except Exception:
            print("  [!]  Node.js install failed. Try: apt install nodejs npm, or nvm install 22, or download from https://nodejs.org")

    # ── undici (proxy support for Node.js fetch) ──
    npm_cmd = shutil.which("npm")
    if npm_cmd:
        npm_root = subprocess.run([npm_cmd, "root", "-g"], capture_output=True, encoding="utf-8", errors="replace", timeout=5).stdout.strip()
        undici_path = os.path.join(npm_root, "undici", "index.js") if npm_root else ""
        if os.path.exists(undici_path):
            print("  ✅ undici already installed (Node.js proxy support)")
        else:
            try:
                subprocess.run([npm_cmd, "install", "-g", "undici"], capture_output=True, encoding="utf-8", errors="replace", timeout=60)
                print("  ✅ undici installed (Node.js proxy support)")
            except Exception:
                print("  -- undici install failed (optional — may not work behind proxies)")

    # ── yt-dlp JS runtime config (YouTube requires external JS runtime) ──
    if shutil.which("node"):
        ytdlp_config_dir = os.path.expanduser("~/.config/yt-dlp")
        ytdlp_config = os.path.join(ytdlp_config_dir, "config")
        needs_config = True
        if os.path.exists(ytdlp_config):
            with open(ytdlp_config, "r") as f:
                if "--js-runtimes" in f.read():
                    needs_config = False
                    print("  ✅ yt-dlp JS runtime already configured")
        if needs_config:
            try:
                os.makedirs(ytdlp_config_dir, exist_ok=True)
                with open(ytdlp_config, "a") as f:
                    f.write("--js-runtimes node\n")
                print("  ✅ yt-dlp configured to use Node.js as JS runtime (YouTube)")
            except Exception:
                print("  -- Could not configure yt-dlp JS runtime (YouTube may not work)")

    # NOTE: twitter-cli, podcast transcription deps, etc. are optional.
    # They are installed via --channels flag, not here.
    # See CHANNEL_INSTALLERS in _cmd_install().


def _install_podcasts_deps():
    """Set up podcast transcription: ffmpeg + yt-dlp + a Whisper API key.

    No per-platform tool is needed — `agent-surf transcribe <url>` downloads
    any episode (yt-dlp), transcodes/chunks it (ffmpeg) and sends it to Whisper.
    """
    import shutil
    from agent_surf.config import Config

    config = Config()
    print("Setting up podcast transcription...")

    # ffmpeg — audio transcode/chunk
    if shutil.which("ffmpeg"):
        print("  ✅ ffmpeg available")
    else:
        print("  -- ffmpeg not found. Install: apt install -y ffmpeg (or brew install ffmpeg)")

    # yt-dlp — episode download
    if shutil.which("yt-dlp"):
        print("  ✅ yt-dlp available")
    else:
        print("  -- yt-dlp not found. Install: pipx install yt-dlp")

    # Whisper provider key (Groq is free)
    has_key = bool(os.environ.get("GROQ_API_KEY")) or bool(config.get("groq_api_key"))
    if has_key:
        print("  ✅ Groq API key configured")
    else:
        print("  -- Groq API key not set. Get free key at https://console.groq.com")
        print("     Then run: agent-surf configure groq-key gsk_xxxxx")

    print('  Transcribe any episode: agent-surf transcribe "<podcast episode URL>"')


def _install_twitter_deps():
    """Install twitter-cli for Twitter search + timeline."""
    import shutil
    import subprocess

    print("Setting up Twitter (twitter-cli)...")
    if shutil.which("twitter"):
        print("  ✅ twitter-cli already installed")
        return
    for tool, cmd in [("pipx", ["pipx", "install", "twitter-cli"]),
                      ("uv", ["uv", "tool", "install", "twitter-cli"])]:
        if shutil.which(tool):
            try:
                subprocess.run(cmd, capture_output=True, encoding="utf-8",
                               errors="replace", timeout=120)
                if shutil.which("twitter"):
                    print("  ✅ twitter-cli installed")
                    return
            except Exception:
                pass
    print("  [!]  twitter-cli install failed. Run: pipx install twitter-cli")


def _install_opencli_deps():
    """Install OpenCLI — cross-platform backend riding the user's Chrome session.

    Desktop-only. The npm package installs automatically; the Chrome
    extension CANNOT be installed programmatically (Chrome security model),
    so we print a one-click guide instead.
    """
    import shutil
    import subprocess

    from agent_surf.backends import (
        OPENCLI_EXTENSION_URL,
        OPENCLI_PACKAGE,
        opencli_status,
        opencli_summary,
    )

    print("Setting up OpenCLI (browser-session backend, desktop only)...")
    st = opencli_status()
    if st.installed and not st.broken:
        print(f"  ✅ {opencli_summary(st)}")
        if not st.ready:
            print(f"  {st.hint}")
        return

    if not shutil.which("npm"):
        print("  [!]  OpenCLI requires Node.js ≥ 20. Install Node first:")
        print("       https://nodejs.org  (or brew install node)")
        return

    try:
        subprocess.run(
            ["npm", "install", "-g", OPENCLI_PACKAGE],
            capture_output=True, encoding="utf-8", errors="replace", timeout=300,
        )
    except Exception:
        pass

    st = opencli_status()
    if st.installed and not st.broken:
        print("  ✅ OpenCLI installed")
        print("  Final step (manual — Chrome security restriction): install the browser extension")
        print(f"    1. Open {OPENCLI_EXTENSION_URL}")
        print('    2. Click "Add to Chrome"')
        print("    3. Run `opencli doctor` to verify the connection")
    else:
        print(f"  [!]  OpenCLI install failed. Run: npm install -g {OPENCLI_PACKAGE}")


def _install_reddit_deps():
    """Set up Reddit — desktop prefers OpenCLI, rdt-cli for servers/legacy.

    No zero-config path exists (anonymous .json blocked, official API
    approval-gated since 2025-11) — every backend needs a logged-in session.
    """
    if _detect_environment() != "server":
        _install_opencli_deps()
        print("  Reddit via OpenCLI (works if you've logged into reddit.com in your browser)")
        import shutil
        if shutil.which("rdt"):
            print("  ✅ Found existing rdt-cli; will remain available as a fallback backend")
        return

    _install_rdt_cli()


def _install_rdt_cli():
    """Install rdt-cli (pinned git source — PyPI lags upstream)."""
    import shutil
    import subprocess

    print("Setting up Reddit (rdt-cli)...")
    if shutil.which("rdt"):
        print("  ✅ rdt-cli already installed")
        return
    for tool, cmd in [
        ("pipx", ["pipx", "install", _RDT_GIT_SOURCE]),
        ("uv", ["uv", "tool", "install", "--from", _RDT_GIT_SOURCE, "rdt-cli"]),
    ]:
        if shutil.which(tool):
            try:
                subprocess.run(cmd, capture_output=True, encoding="utf-8",
                               errors="replace", timeout=120)
                if shutil.which("rdt"):
                    print("  ✅ rdt-cli installed")
                    return
            except Exception:
                pass
    print(f"  [!]  rdt-cli install failed. Run: pipx install '{_RDT_GIT_SOURCE}'")


def _install_system_deps_safe():
    """Safe mode: check what's installed, print instructions for what's missing."""
    import shutil

    print("Checking system dependencies (safe mode — no auto-install)...")

    deps = [
        ("gh", ["gh"], "GitHub CLI", "https://cli.github.com — or: apt install gh / brew install gh"),
        ("node", ["node", "npm"], "Node.js", "https://nodejs.org — or: apt install nodejs npm"),
    ]

    missing = []
    for name, binaries, label, install_hint in deps:
        found = any(shutil.which(b) for b in binaries)
        if found:
            print(f"  ✅ {label} already installed")
        else:
            print(f"  -- {label} not found")
            missing.append((label, install_hint))

    if missing:
        print()
        print("  To install missing dependencies manually:")
        for label, hint in missing:
            print(f"    {label}: {hint}")
    else:
        print("  All system dependencies are installed!")


def _install_system_deps_dryrun():
    """Dry-run: just show what would be checked/installed."""
    import shutil

    print("[dry-run] System dependency check:")

    checks = [
        ("gh CLI", ["gh"], "apt install gh / brew install gh"),
        ("Node.js", ["node"], "curl NodeSource setup | bash + apt install nodejs"),
    ]

    for label, binaries, method in checks:
        found = any(shutil.which(b) for b in binaries)
        if found:
            print(f"  ✅ {label}: already installed, skip")
        else:
            print(f"  {label}: would install via: {method}")



def _install_mcporter():
    """Install mcporter and configure Exa search."""
    import shutil
    import subprocess

    print("Setting up mcporter (search backend)...")

    if shutil.which("mcporter"):
        print("  ✅ mcporter already installed")
    else:
        # Check for npm/npx
        if not shutil.which("npm") and not shutil.which("npx"):
            print("  [!]  mcporter requires Node.js. Install Node.js first:")
            print("     https://nodejs.org/ or: curl -fsSL https://fnm.vercel.app/install | bash")
            return
        try:
            subprocess.run(
                ["npm", "install", "-g", "mcporter"],
                capture_output=True, encoding="utf-8", errors="replace", timeout=120,
            )
            if shutil.which("mcporter"):
                print("  ✅ mcporter installed")
            else:
                print("  [X] mcporter install failed. Retry: npm install -g mcporter (check network/timeout), or try: npx mcporter@latest list")
                return
        except Exception as e:
            print(f"  [X] mcporter install failed: {e}")
            return

    # Configure Exa MCP (free, no key needed)
    try:
        r = subprocess.run(
            ["mcporter", "config", "list"], capture_output=True, encoding="utf-8", errors="replace", timeout=5
        )
        if "exa" not in r.stdout:
            subprocess.run(
                ["mcporter", "config", "add", "exa", "https://mcp.exa.ai/mcp"],
                capture_output=True, encoding="utf-8", errors="replace", timeout=10,
            )
            print("  ✅ Exa search configured (free, no API key needed)")
        else:
            print("  ✅ Exa search already configured")
    except Exception:
        print("  [!]  Could not configure Exa. Run manually: mcporter config add exa https://mcp.exa.ai/mcp")

    # NOTE: optional channel tools are installed via the --channels flag.


def _install_mcporter_safe():
    """Safe mode: check mcporter status, print instructions."""
    import shutil

    print("Checking mcporter (safe mode)...")

    if shutil.which("mcporter"):
        print("  ✅ mcporter already installed")
        print("  To configure Exa search: mcporter config add exa https://mcp.exa.ai/mcp")
    else:
        print("  -- mcporter not installed")
        print("  To install: npm install -g mcporter")
        print("  Then configure Exa: mcporter config add exa https://mcp.exa.ai/mcp")


def _detect_environment():
    """Auto-detect if running on local computer or server."""
    import os

    # Check common server indicators
    indicators = 0

    # SSH session
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"):
        indicators += 2

    # Docker / container
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        indicators += 2

    # No display (headless)
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        indicators += 1

    # Cloud VM identifiers
    for cloud_file in ["/sys/hypervisor/uuid", "/sys/class/dmi/id/product_name"]:
        if os.path.exists(cloud_file):
            try:
                with open(cloud_file) as f:
                    content = f.read().lower()
                if any(x in content for x in ["amazon", "google", "microsoft", "digitalocean", "linode", "vultr", "hetzner"]):
                    indicators += 2
            except Exception:
                pass

    # systemd-detect-virt
    try:
        import subprocess
        result = subprocess.run(["systemd-detect-virt"], capture_output=True, encoding="utf-8", errors="replace", timeout=3)
        if result.returncode == 0 and result.stdout.strip() != "none":
            indicators += 1
    except Exception:
        pass

    return "server" if indicators >= 2 else "local"


def _cmd_configure(args):
    """Set a config value and test it, or auto-extract from browser."""
    import shutil
    from agent_surf.config import Config

    config = Config()

    # ── Auto-extract from browser ──
    if args.from_browser:
        from agent_surf.cookie_extract import configure_from_browser

        browser = args.from_browser
        print(f"Extracting cookies from {browser}...")
        print()

        results = configure_from_browser(browser, config)

        found_any = False
        for platform, success, message in results:
            if success:
                print(f"  ✅ {platform}: {message}")
                found_any = True
            else:
                print(f"  -- {platform}: {message}")

        print()
        if found_any:
            print("✅ Cookies configured! Run `agent-surf doctor` to see updated status.")
        else:
            print(f"No cookies found. Make sure you're logged into the platforms in {browser}.")
        return

    # ── Manual configure ──
    if not args.key:
        print("Usage: agent-surf configure <key> <value>")
        print("   or: agent-surf configure --from-browser chrome")
        return

    value = " ".join(args.value) if args.value else ""
    if not value:
        print(f"Missing value for {args.key}")
        return

    if args.key == "proxy":
        # Generic network proxy for restricted environments. Nothing reads
        # this key at runtime — agents read it back and export HTTP(S)_PROXY
        # before invoking upstream tools (see docs/install.md).
        config.set("proxy", value)
        print("✅ Proxy saved (Agent sets HTTP_PROXY/HTTPS_PROXY when accessing Reddit/Twitter and other restricted networks)")

    elif args.key == "twitter-cookies":
        # Accept two formats:
        # 1. auth_token ct0 (two separate values)
        # 2. Full cookie header string: "auth_token=xxx; ct0=yyy; ..."
        auth_token, ct0 = _parse_twitter_cookie_input(value)

        if auth_token and ct0:
            config.set("twitter_auth_token", auth_token)
            config.set("twitter_ct0", ct0)

            # Sync credentials to twitter-cli env
            print("✅ Twitter cookies configured!")

            print("Testing Twitter access...", end=" ")
            try:
                import subprocess
                twitter_bin = shutil.which("twitter")
                if not twitter_bin:
                    print("[!] twitter-cli not installed. Run: pipx install twitter-cli")
                else:
                    import os
                    env = os.environ.copy()
                    env["TWITTER_AUTH_TOKEN"] = auth_token
                    env["TWITTER_CT0"] = ct0
                    result = subprocess.run(
                        [twitter_bin, "status"],
                        capture_output=True, encoding="utf-8", errors="replace", timeout=15,
                        env=env,
                    )
                    output = (result.stdout or "") + (result.stderr or "")
                    if "ok: true" in output:
                        print("✅ Twitter access works!")
                    else:
                        print("[!] Auth check failed (cookies might be wrong)")
            except Exception as e:
                print(f"[X] Failed: {e}")
        else:
            print("[X] Could not find auth_token and ct0 in your input.")
            print("   Accepted formats:")
            print("   1. agent-surf configure twitter-cookies AUTH_TOKEN CT0")
            print('   2. agent-surf configure twitter-cookies "auth_token=xxx; ct0=yyy; ..."')

    elif args.key == "youtube-cookies":
        config.set("youtube_cookies_from", value)
        print(f"✅ YouTube cookie source configured: {value}")
        print("   yt-dlp will use cookies from this browser for age-restricted/member videos.")

    elif args.key == "producthunt-token":
        config.set("producthunt_token", value)
        print("✅ Product Hunt token configured!")

    elif args.key == "github-token":
        config.set("github_token", value)
        print(f"✅ GitHub token configured!")

    elif args.key == "groq-key":
        config.set("groq_api_key", value)
        print(f"✅ Groq key configured!")

    elif args.key == "openai-key":
        config.set("openai_api_key", value)
        print(f"✅ OpenAI key configured!")


def _cmd_transcribe(args):
    """Transcribe a URL or local audio file via Whisper (Groq → OpenAI fallback)."""
    from pathlib import Path

    from agent_surf.transcribe import TranscribeError, transcribe

    try:
        text = transcribe(args.source, provider=args.provider)
    except TranscribeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"✅ Transcript written to {args.output}")
    else:
        print(text)


def _parse_twitter_cookie_input(value: str):
    """Parse Twitter cookie input from either separate values or a cookie header."""
    auth_token = None
    ct0 = None

    if "auth_token=" in value and "ct0=" in value:
        # Full cookie string — parse it.
        for part in value.replace(";", " ").split():
            if part.startswith("auth_token="):
                auth_token = part.split("=", 1)[1]
            elif part.startswith("ct0="):
                ct0 = part.split("=", 1)[1]
    elif len(value.split()) == 2 and "=" not in value:
        # Two separate values: AUTH_TOKEN CT0.
        parts = value.split()
        auth_token = parts[0]
        ct0 = parts[1]

    return auth_token, ct0


def _cmd_uninstall(args):
    """Remove all Agent Surf config, tokens, and skill files."""
    import shutil
    import subprocess

    dry_run = args.dry_run
    keep_config = args.keep_config

    print()
    print("Agent Surf Uninstaller")
    print("=" * 40)

    if dry_run:
        print("DRY RUN — showing what would be removed (no changes)")
        print()

    removed_any = False

    # ── 1. Config directory (~/.agent-surf/) ──
    config_dir = os.path.expanduser("~/.agent-surf")
    if not keep_config:
        if os.path.isdir(config_dir):
            if dry_run:
                print(f"[dry-run] Would remove config directory: {config_dir}")
                print("          (contains config.yaml with all tokens/cookies/API keys)")
            else:
                try:
                    shutil.rmtree(config_dir)
                    print(f"  Removed config directory: {config_dir}")
                    removed_any = True
                except Exception as e:
                    print(f"  Could not remove {config_dir}: {e}")
        else:
            print(f"  Config directory not found (already clean): {config_dir}")
    else:
        print(f"  Skipping config directory (--keep-config): {config_dir}")

    # ── 2. Skill files ──
    skill_dirs = [
        ("~/.openclaw/skills/agent-surf", "OpenClaw"),
        ("~/.claude/skills/agent-surf", "Claude Code"),
        ("~/.agents/skills/agent-surf", "Agent"),
    ]

    for skill_path_template, platform_name in skill_dirs:
        skill_path = os.path.expanduser(skill_path_template)
        if os.path.isdir(skill_path):
            if dry_run:
                print(f"[dry-run] Would remove {platform_name} skill: {skill_path}")
            else:
                try:
                    if os.path.islink(skill_path):
                        os.unlink(skill_path)
                    else:
                        shutil.rmtree(skill_path)
                    print(f"  Removed {platform_name} skill: {skill_path}")
                    removed_any = True
                except Exception as e:
                    print(f"  Could not remove {skill_path}: {e}")

    # ── 3. mcporter MCP entries ──
    if shutil.which("mcporter"):
        for mcp_name in ("exa",):
            try:
                r = subprocess.run(
                    ["mcporter", "list"], capture_output=True, encoding="utf-8", errors="replace", timeout=10
                )
                if mcp_name in r.stdout:
                    if dry_run:
                        print(f"[dry-run] Would remove mcporter entry: {mcp_name}")
                    else:
                        subprocess.run(
                            ["mcporter", "config", "remove", mcp_name],
                            capture_output=True, encoding="utf-8", errors="replace", timeout=10,
                        )
                        print(f"  Removed mcporter entry: {mcp_name}")
                        removed_any = True
            except Exception:
                pass

    # ── 4. Summary and optional steps ──
    print()
    if dry_run:
        print("Dry run complete. No changes were made.")
        print("Run without --dry-run to actually remove the above.")
    else:
        if removed_any:
            print("Agent Surf data removed.")
        else:
            print("Nothing to remove — already clean.")

    print()
    print("Optional: remove the Agent Surf Python package itself:")
    print("  pip uninstall agent-surf")
    print()
    print("Optional: remove tools installed by Agent Surf:")
    print("  npm uninstall -g mcporter")
    print("  pipx uninstall twitter-cli")
    print("  npm uninstall -g undici")


def _cmd_doctor(args=None):
    from agent_surf.config import Config
    from agent_surf.doctor import check_all, format_report
    try:
        from rich import print as rprint
    except ImportError:
        rprint = print
    config = Config()
    results = check_all(config)

    if args is not None and getattr(args, "json", False):
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    rprint(format_report(results))

    # Auto-install skill if not already present (fixes #154)
    _install_skill()


def _cmd_setup():
    from agent_surf.config import Config

    config = Config()
    print()
    print("Agent Surf Setup")
    print("=" * 40)
    print()

    # Step 1: Exa (via mcporter, no API key required)
    import shutil
    import subprocess

    print("[Recommended] Web search — Exa (via mcporter)")
    print("  Free, no API key required")

    if not shutil.which("mcporter"):
        print("  Status: -- mcporter not installed")
        print("  Install: npm install -g mcporter")
        print("  Then: mcporter config add exa https://mcp.exa.ai/mcp")
        print()
    else:
        try:
            r = subprocess.run(
                ["mcporter", "config", "list"], capture_output=True, encoding="utf-8", errors="replace", timeout=10
            )
            if "exa" in r.stdout.lower():
                print("  Status: ✅ configured")
            else:
                print("  Status: -- not configured")
                setup_now = input("  Auto-configure Exa now? [Y/n]: ").strip().lower()
                if setup_now in ("", "y", "yes"):
                    add_r = subprocess.run(
                        ["mcporter", "config", "add", "exa", "https://mcp.exa.ai/mcp"],
                        capture_output=True, encoding="utf-8", errors="replace", timeout=10,
                    )
                    if add_r.returncode == 0:
                        print("  ✅ Exa configured")
                    else:
                        print("  [!] Auto-configure failed. Run manually:")
                        print("     mcporter config add exa https://mcp.exa.ai/mcp")
        except Exception:
            print("  [!] Could not check Exa config. Run manually:")
            print("     mcporter config add exa https://mcp.exa.ai/mcp")
        print()

    # Step 2: GitHub token
    print("[Optional] GitHub Token — higher API rate limits")
    print("  No token: 60 req/hour | With token: 5000 req/hour")
    print("  Get one: https://github.com/settings/tokens (no permissions required)")
    current = config.get("github_token")
    if current:
        print(f"  Status: ✅ configured")
    else:
        key = input("  GITHUB_TOKEN (Enter to skip): ").strip()
        if key:
            config.set("github_token", key)
            print("  ✅ GitHub API raised to 5000 req/hour!")
        else:
            print("  Skipped. Public API still works.")
    print()

    # Step 3: Reddit — rdt-cli
    print("[Info] Reddit — login required (no zero-config path). Desktop: OpenCLI; or rdt-cli:")
    print(f"  Install: pipx install '{_RDT_GIT_SOURCE}'")
    print("  Then run: rdt login (log into reddit.com in your browser first)")
    print()

    # Step 4: Groq (Whisper)
    print("[Optional] Groq API — speech-to-text when videos have no subtitles")
    print("  Free tier available. Sign up: https://console.groq.com")
    current = config.get("groq_api_key")
    if current:
        print(f"  Status: ✅ configured")
    else:
        key = input("  GROQ_API_KEY (Enter to skip): ").strip()
        if key:
            config.set("groq_api_key", key)
            print("  ✅ Speech-to-text enabled!")
        else:
            print("  Skipped")
    print()

    # Summary
    print("=" * 40)
    print(f"✅ Configuration saved to {config.config_path}")
    print("Run agent-surf doctor for full status")
    print()


def _classify_update_error(exc):
    """Classify update-check errors for user-friendly diagnostics."""
    import requests

    if isinstance(exc, requests.exceptions.Timeout):
        return "timeout"
    if isinstance(exc, requests.exceptions.ConnectionError):
        msg = str(exc).lower()
        dns_markers = [
            "name or service not known",
            "temporary failure in name resolution",
            "nodename nor servname",
            "getaddrinfo failed",
            "name resolution",
            "dns",
        ]
        if any(marker in msg for marker in dns_markers):
            return "dns"
        return "connection"
    if isinstance(exc, requests.exceptions.HTTPError):
        return "http"
    return "unknown"


def _update_error_text(kind):
    """Map internal error kinds to user-facing text."""
    mapping = {
        "timeout": "Network timeout",
        "dns": "DNS resolution failed",
        "rate_limit": "GitHub API rate limit",
        "connection": "Network connection failed",
        "server_error": "GitHub service temporarily unavailable",
        "http": "HTTP request failed",
        "unknown": "Unknown network error",
    }
    return mapping.get(kind, "Request failed")


def _classify_github_response_error(resp):
    """Classify non-200 GitHub responses that merit special handling."""
    if resp is None:
        return "unknown"
    if resp.status_code == 429:
        return "rate_limit"
    if resp.status_code == 403:
        remaining = resp.headers.get("X-RateLimit-Remaining", "")
        if remaining == "0":
            return "rate_limit"
        try:
            message = resp.json().get("message", "").lower()
            if "rate limit" in message:
                return "rate_limit"
        except Exception:
            pass
    if 500 <= resp.status_code < 600:
        return "server_error"
    return None


def _github_get_with_retry(url, timeout=10, retries=3, sleeper=time.sleep):
    """GET GitHub API with retry/backoff and basic error classification."""
    import requests

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            if attempt >= retries:
                return None, _classify_update_error(exc), attempt
            sleeper(2 ** (attempt - 1))
            continue

        err_kind = _classify_github_response_error(resp)
        if err_kind in ("rate_limit", "server_error"):
            if attempt >= retries:
                return None, err_kind, attempt
            delay = 2 ** (attempt - 1)
            retry_after = resp.headers.get("Retry-After")
            if err_kind == "rate_limit" and retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except Exception:
                    pass
            sleeper(delay)
            continue

        return resp, None, attempt

    return None, "unknown", retries


#: Full update = package + upstream tools + skill. The one-liner walks an
#: agent through all three (docs/update.md); bare pip only updates the package.
_UPDATE_INSTRUCTIONS = (
    "How to update (recommended — copy this line to your AI Agent for a full update of package + upstream tools + skill):\n"
    "  Update Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md\n"
    "Package only (does not update upstream tools or skill):\n"
    "  pip install --upgrade https://github.com/rijuld/agent-surf/archive/main.zip"
)


def _is_newer_version(remote: str, local: str) -> bool:
    """True if remote is strictly newer than local (semantic compare).

    A plain != would tell users "update available" when their local build is
    AHEAD of the latest release (e.g. installed from main during a release
    window) — and walk them into a downgrade.
    """
    def parse(v):
        try:
            return tuple(int(x) for x in v.strip().split("."))
        except ValueError:
            return None

    r, l = parse(remote), parse(local)
    if r is None or l is None:
        return remote != local  # unparseable — fall back to old behavior
    return r > l


def _cmd_check_update():
    """Check for newer versions on GitHub."""
    from agent_surf import __version__

    print(f"Current version: v{__version__}")
    release_url = "https://api.github.com/repos/rijuld/agent-surf/releases/latest"
    commit_url = "https://api.github.com/repos/rijuld/agent-surf/commits/main"

    # Fetch latest release with retry/backoff.
    resp, err, attempts = _github_get_with_retry(release_url, timeout=10, retries=3)
    if err:
        print(f"[!] Could not check for updates ({_update_error_text(err)}, retried {attempts} time(s))")
        return "error"

    if resp.status_code == 200:
        data = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        body = data.get("body", "")

        if latest and _is_newer_version(latest, __version__):
            print(f"Latest version: v{latest} ← update available!")
            if body:
                print()
                print("What's new:")
                # Show first 20 lines of release notes
                for line in body.strip().split("\n")[:20]:
                    print(f"  {line}")
            print()
            print(_UPDATE_INSTRUCTIONS)
            return "update_available"
        print(f"✅ Already on the latest version")
        return "up_to_date"

    release_err = _classify_github_response_error(resp)
    if release_err == "rate_limit":
        print("[!] Could not check for updates (GitHub API rate limit — try again later)")
        return "error"

    # No releases yet, fall back to latest main commit.
    resp2, err2, attempts2 = _github_get_with_retry(commit_url, timeout=10, retries=2)
    if err2:
        print(f"[!] Could not check for updates ({_update_error_text(err2)}, retried {attempts + attempts2} time(s))")
        return "error"
    if resp2.status_code == 200:
        commit = resp2.json()
        sha = commit.get("sha", "")[:7]
        msg = commit.get("commit", {}).get("message", "").split("\n")[0]
        date = commit.get("commit", {}).get("committer", {}).get("date", "")[:10]
        print(f"Latest commit: {sha} ({date}) {msg}")
        print()
        print(_UPDATE_INSTRUCTIONS)
        return "unknown"

    commit_err = _classify_github_response_error(resp2)
    if commit_err == "rate_limit":
        print("[!] Could not check for updates (GitHub API rate limit — try again later)")
        return "error"

    print(f"[!] Could not check for updates (GitHub returned {resp2.status_code})")
    return "error"


def _cmd_watch():
    """Quick health check + update check, designed for scheduled tasks.

    Only outputs problems. If everything is fine, outputs a single line.
    """
    from agent_surf.config import Config
    from agent_surf.doctor import check_all
    from agent_surf import __version__

    config = Config()
    issues = []

    # Check channels
    results = check_all(config)
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    # Find broken channels (were working, now broken)
    for key, r in results.items():
        if r["status"] in ("off", "error"):
            issues.append(f"[X] {r['name']}：{r['message']}")
        elif r["status"] == "warn":
            issues.append(f"[!] {r['name']}：{r['message']}")

    # Check for updates
    update_available = False
    new_version = ""
    release_body = ""
    resp, err, _attempts = _github_get_with_retry(
        "https://api.github.com/repos/rijuld/agent-surf/releases/latest",
        timeout=10,
        retries=2,
    )
    if not err and resp and resp.status_code == 200:
        data = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        if latest and _is_newer_version(latest, __version__):
            update_available = True
            new_version = latest
            release_body = data.get("body", "")

    # Output
    if not issues and not update_available:
        print(f"Agent Surf: All systems go ({ok}/{total} channels available, v{__version__} is latest)")
        return

    print(f"Agent Surf monitoring report")
    print(f"=" * 40)
    print(f"Version: v{__version__}  |  Channels: {ok}/{total}")

    if issues:
        print()
        for issue in issues:
            print(f"  {issue}")

    if update_available:
        print()
        print(f"Update available: v{new_version}")
        if release_body:
            for line in release_body.strip().split("\n")[:10]:
                print(f"    {line}")
        print("  To update (one line to your Agent for a full update):")
        print("    Update Agent Surf: https://raw.githubusercontent.com/rijuld/agent-surf/main/docs/update.md")


if __name__ == "__main__":
    main()
