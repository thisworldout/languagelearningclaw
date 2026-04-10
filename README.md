# languagelearningclaw

Telegram + OpenClaw + learning backend: CEFR-aware vocabulary from user sentences, optional ElevenLabs audio, weekly summaries.

## Quick start (local)

1. Copy `.env.example` to `.env` and set `DATABASE_URL` (or use Docker only).
2. `python3 -m pip install -r backend/requirements.txt` and `python3 -m spacy download en_core_web_sm`
3. Start Postgres, then:

```bash
cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

4. `curl http://127.0.0.1:8000/health`

Example analyze (requires `X-API-Key`):

```bash
curl -s http://127.0.0.1:8000/v1/analyze-sentence \
  -H "X-API-Key: dev-insecure-change-me" \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id":123,"sentence":"The meeting was postponed unexpectedly.","language":"en"}'
```

## Docker (Featherless / VPS)

```bash
docker compose up -d --build
```

HTTPS: see [deploy/Caddyfile.example](deploy/Caddyfile.example) (reverse proxy to port 8000). Run OpenClaw on the host or a separate process; point its tools at `http://127.0.0.1:8000` or `http://api:8000` on the Docker network.

Optional Telegram bot (same compose file):

```bash
export TELEGRAM_BOT_TOKEN=... API_KEY=...
docker compose --profile telegram up -d --build
```

## OpenClaw & ClawMetry

See [docs/openclaw.md](docs/openclaw.md) and [openclaw/http-tools.json](openclaw/http-tools.json).
