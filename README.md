# languagelearningclaw

Language assistant stack: **Telegram** for chat, **OpenClaw** for routing and tools, and a **Python/FastAPI learning backend** that owns pedagogy—CEFR-aware vocabulary from sentences you send, optional **ElevenLabs** voice lessons, weekly summaries, and Whisper STT for incoming voice.

| Layer | Role |
|--------|------|
| Telegram | User messaging (text / voice) |
| OpenClaw | Session routing, tool calls, replies (see `docs/openclaw.md`) |
| This API | Lemma extraction, ranking, persistence, lesson scripts |
| LLM (OpenAI-compatible) | Explanations from ranked words—not the only word-picker |
| ElevenLabs | TTS for short lesson audio |

```
Telegram → OpenClaw → Learning API → Postgres
                           ↓
                    LLM / ElevenLabs
```

## Requirements

- Python 3.12+ (3.13 supported; `spacy` pinned accordingly)
- PostgreSQL 16+ (or use Docker Compose)
- Optional: `OPENAI_API_KEY` for explanations + transcription; `ELEVENLABS_*` for TTS

## Quick start (local)

1. Copy `.env.example` to `.env` and set `DATABASE_URL` (and API keys if you use LLM/TTS/STT).

2. Install dependencies and the English spaCy model:

   ```bash
   python3 -m pip install -r backend/requirements.txt
   python3 -m spacy download en_core_web_sm
   ```

3. Start Postgres, then the API:

   ```bash
   cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8000
   ```

4. Health check:

   ```bash
   curl -s http://127.0.0.1:8000/health
   ```

5. Analyze a sentence (`X-API-Key` must match `API_KEY` in `.env`):

   ```bash
   curl -s http://127.0.0.1:8000/v1/analyze-sentence \
     -H "X-API-Key: dev-insecure-change-me" \
     -H "Content-Type: application/json" \
     -d '{"telegram_user_id":123,"sentence":"The meeting was postponed unexpectedly.","language":"en"}'
   ```

## Environment variables

See [`.env.example`](.env.example). Main entries:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string |
| `API_KEY` | Required on all `/v1/*` requests as header `X-API-Key` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `LLM_MODEL` | Explanations + Whisper STT |
| `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` | Voice lesson generation |
| `TELEGRAM_BOT_TOKEN` | Only for the standalone `telegram_bot` (optional) |

## HTTP API (summary)

All `/v1/*` routes require header `X-API-Key: <API_KEY>`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness (no auth) |
| `POST` | `/v1/analyze-sentence` | Rank words, save progress, return Markdown explanation |
| `GET` | `/v1/profile/{telegram_user_id}` | Learner profile |
| `POST` | `/v1/profile` | Create/update profile (level A0–B2, languages) |
| `POST` | `/v1/generate-audio` | ElevenLabs MP3 as base64 from script or word list |
| `GET` | `/v1/weekly-summary/{telegram_user_id}` | Rule-based week stats + optional LLM polish |
| `POST` | `/v1/transcribe` | Multipart audio → text (Whisper) |

OpenClaw integration contract: [`openclaw/http-tools.json`](openclaw/http-tools.json).

## Docker (VPS / Featherless)

```bash
docker compose up -d --build
```

HTTPS front end: [`deploy/Caddyfile.example`](deploy/Caddyfile.example). Keep the API on localhost or a private Docker network; expose only what you need. OpenClaw can call `http://api:8000` from the same Compose network or `http://127.0.0.1:8000` on the host.

Optional direct Telegram bot (bypasses OpenClaw for debugging):

```bash
export TELEGRAM_BOT_TOKEN=... API_KEY=...
docker compose --profile telegram up -d --build
```

## OpenClaw and ClawMetry

- [docs/openclaw.md](docs/openclaw.md) — tool wiring, voice replies, ClawMetry (observability lives on the OpenClaw process).

## Repository layout

- `backend/` — FastAPI app and Dockerfile
- `telegram_bot/` — Minimal polling bot calling the API
- `openclaw/` — HTTP tool descriptions for agents
- `deploy/` — Example reverse proxy config
- `docs/` — OpenClaw-specific notes

## License

Add a license file if you open-source the repo.
