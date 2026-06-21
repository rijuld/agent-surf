# Groq Whisper Setup Guide

## What it does
When YouTube videos have no subtitles, or to transcribe a podcast episode, use Groq's Whisper API for speech-to-text. Groq offers a free tier.

## Steps the Agent can automate

1. Check if already configured:
```bash
agent-surf doctor | grep -i "groq\|whisper"
```

2. If user provided a key, write to config:
```python
from agent_surf.config import Config
c = Config()
c.set("groq_api_key", "USER_PROVIDED_KEY")
```

3. Test (optional):
```bash
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer USER_PROVIDED_KEY" \
  -o /dev/null -w "%{http_code}"
```
Returns 200 = working

## Manual steps for the user

Tell the user:

> Video speech-to-text needs a Groq API Key (free).
>
> Steps:
> 1. Open https://console.groq.com
> 2. Sign up with Google or email
> 3. Click "API Keys" on the left
> 4. Click "Create API Key"
> 5. Copy the key and send it to me
>
> Groq free tier is enough for daily use.

## After receiving the key

1. Write config: `config.set("groq_api_key", key)`
2. Test API availability
3. Reply: "✅ Speech-to-text enabled! I can now extract content from videos without subtitles."
