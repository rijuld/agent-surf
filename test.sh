#!/bin/bash
# Agent Surf full integration test
# Usage: bash test.sh
# Runs on any machine with Python 3.10+

set -e

echo "╔════════════════════════════════════════════╗"
echo "║       Agent Surf Full Test                ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# ── 1. Prepare clean environment ──
echo "📦 Creating test environment..."
TEST_DIR=$(mktemp -d)
python3 -m venv "$TEST_DIR/venv"
source "$TEST_DIR/venv/bin/activate"

# ── 2. Install ──
echo "📥 Installing from GitHub..."
pip install -q https://github.com/rijuld/agent-surf/archive/main.zip 2>&1 | tail -1
echo ""

# ── 3. Auto-configure ──
echo "⚙️  Running install..."
agent-surf install --env=auto 2>&1
echo ""

# ── 4. Diagnostics ──
echo "🩺 Running doctor..."
agent-surf doctor 2>&1
echo ""

# ── 5. Individual tests ──
PASS=0
FAIL=0
SKIP=0

test_it() {
    local name="$1"
    shift
    echo -n "  $name ... "
    output=$(eval "$@" 2>&1) || true
    if echo "$output" | grep -q "📖\|🔗\|http"; then
        echo "✅"
        PASS=$((PASS+1))
    elif echo "$output" | grep -q "⚠️\|not installed\|not configured"; then
        echo "⏭️  (skipped — missing dependency)"
        SKIP=$((SKIP+1))
    else
        echo "❌"
        echo "    $(echo "$output" | head -2)"
        FAIL=$((FAIL+1))
    fi
}

echo "📖 Read tests"
test_it "Web" "agent-surf read 'https://example.com'"
test_it "GitHub" "agent-surf read 'https://github.com/rijuld/agent-surf'"
test_it "YouTube" "agent-surf read 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'"
test_it "Hacker News" "agent-surf read 'https://news.ycombinator.com/item?id=1'"
test_it "RSS" "agent-surf read 'https://hnrss.org/frontpage'"
test_it "Twitter" "agent-surf read 'https://x.com/elonmusk/status/1893797839927353448'"
test_it "Reddit" "agent-surf read 'https://www.reddit.com/r/LocalLLaMA/hot'"

echo ""
echo "🔍 Search tests"
test_it "Web search" "agent-surf search 'best AI agent framework' -n 2"
test_it "GitHub search" "agent-surf search-github 'yt-dlp' -n 2"
test_it "Twitter search" "agent-surf search-twitter 'AI agent' -n 2"
test_it "Reddit search" "agent-surf search-reddit 'machine learning' -n 2"
test_it "YouTube search" "agent-surf search-youtube 'AI tutorial' -n 2"
test_it "Hacker News search" "agent-surf search-hackernews 'AI' -n 2"
test_it "Product Hunt search" "agent-surf search-producthunt 'AI' -n 2"

echo ""
echo "════════════════════════════════════════════"
echo "  ✅ Passed: $PASS   ❌ Failed: $FAIL   ⏭️  Skipped: $SKIP"
echo "════════════════════════════════════════════"

# ── 6. Cleanup ──
deactivate 2>/dev/null || true
rm -rf "$TEST_DIR"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 All passed!"
else
    echo ""
    echo "⚠️  $FAIL test(s) failed — check the output above"
    exit 1
fi
