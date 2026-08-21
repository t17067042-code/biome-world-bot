# Biome World Telegram Bot

## Railway deploy (24/7)

1. Open https://railway.com/new
2. Deploy from GitHub → `t17067042-code/biome-world-bot`
3. Set variables:
   - `BOT_TOKEN` = your bot token
   - `MP_PUBLIC_URL` = https://YOUR-APP.up.railway.app (after first deploy)
4. Generate domain in Settings → Networking

## Local

```bash
export BOT_TOKEN=...
pip install -r requirements.txt
python standalone_bot.py
```

## Commands

- `/start` — settlement
- `/game` — Biome World RTS (needs static_game.html + MP_PUBLIC_URL)
