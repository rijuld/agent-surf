# Video & Podcasts

Subtitles and transcripts for YouTube and podcasts (Apple Podcasts).

## YouTube (yt-dlp)

### Get video metadata

```bash
yt-dlp --dump-json "URL"
```

### Download subtitles

```bash
# Download subtitles (no video download)
yt-dlp --write-sub --write-auto-sub --sub-lang "en" --skip-download -o "/tmp/%(id)s" "URL"

# Then read .vtt file
cat /tmp/VIDEO_ID.*.vtt
```

### Get comments

```bash
# Extract comments (best-effort, not guaranteed complete)
yt-dlp --write-comments --skip-download --write-info-json \
  --extractor-args "youtube:max_comments=20" \
  -o "/tmp/%(id)s" "URL"
# Comments in .info.json comments field
```

### Search videos

```bash
yt-dlp --dump-json "ytsearch5:query"
```

> **Subtitles note:** Manually uploaded subtitles extract reliably; auto-generated may have duplicate lines — post-process if needed.
> **Comments note:** `--write-comments` uses web scraping (not YouTube Data API) — some comments may be missing.

### No subtitles fallback: Whisper audio transcription

```bash
# When a video has no subtitles: download audio and transcribe with Whisper (free Groq key)
agent-surf transcribe "https://www.youtube.com/watch?v=VIDEO_ID"
agent-surf transcribe ./local_audio.mp3 -o /tmp/transcript.txt
```

> Configure key first: `agent-surf configure groq-key gsk_xxx` (free, console.groq.com)
> or `agent-surf configure openai-key sk-xxx`. Default auto mode: groq falls back to openai on failure.

## Podcasts (Apple Podcasts)

Discovery uses Apple's public iTunes Search API (no key). Episodes are plain
audio URLs, so transcription reuses the same Whisper pipeline as YouTube.

### Find a podcast

```bash
# Search podcasts by name/topic (returns feedUrl, genre, episode count, etc.)
curl -s "https://itunes.apple.com/search?media=podcast&limit=10&term=QUERY"
```

```python
from agent_surf.channels.podcasts import PodcastsChannel

ch = PodcastsChannel()
for p in ch.search("acquired", limit=5):
    print(f"{p['name']} — {p['artist']}  ({p['feed_url']})")
```

### Transcribe an episode

```bash
# Works on an Apple Podcasts episode page, an enclosure audio URL, or a local file
agent-surf transcribe "https://podcasts.apple.com/us/podcast/.../id...?i=EPISODE_ID"
agent-surf transcribe "https://example.com/episode.mp3" -o /tmp/episode.txt
```

### Prerequisites

1. **ffmpeg:** `brew install ffmpeg` (macOS) / `apt install -y ffmpeg` (Linux)
2. **yt-dlp:** `pipx install yt-dlp` (downloads episode audio)
3. **Groq API Key** (free): https://console.groq.com/keys
4. **Configure key:** `agent-surf configure groq-key YOUR_KEY`

### Check status

```bash
agent-surf doctor
```

> Long episodes are auto-chunked (10-min segments) and joined into one transcript.

## Selection guide

| Scenario | Recommended tool |
|----------|------------------|
| YouTube subtitles | yt-dlp |
| YouTube video has no subtitles | agent-surf transcribe |
| Podcast discovery | iTunes Search API / PodcastsChannel.search |
| Podcast episode → text | agent-surf transcribe |
| Any local/remote audio file → text | agent-surf transcribe |
