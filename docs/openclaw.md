# OpenClaw + ClawMetry

## Learning backend tools

Register HTTP tools (or equivalent plugins) so OpenClaw can call the API defined in [openclaw/http-tools.json](../openclaw/http-tools.json).

- From the same host as OpenClaw, use `http://127.0.0.1:8000` if the API listens on localhost.
- From Docker, use service name `http://api:8000`.
- Always send `X-API-Key` matching `API_KEY` / `LEARNING_API_KEY`.

The agent should pass the Telegram `user.id` as `telegram_user_id` on every call so the backend can scope data.

## Voice replies

After `generate_audio`, decode `base64_audio` (MP3) and attach as a voice note. OpenClaw Telegram docs describe `[[audio_as_voice]]` and media payloads for voice-note delivery.

## ClawMetry

[ClawMetry](https://clawmetry.com) connects to **OpenClaw** for token usage, sessions, and tool visibility — not to this Python API.

1. Create a ClawMetry account during OpenClaw integration.
2. Follow ClawMetry’s OpenClaw connection steps (API keys / agent ID as documented on their site).
3. Use dashboards to watch tool calls to `analyze_sentence` and catch runaway LLM loops.

Set any ClawMetry variables on the **OpenClaw process**, not inside `docker-compose` for the learning API unless you co-locate them.

## Featherless / VPS

Run `docker compose up -d` on the VPS: Postgres + `api` service. Optionally `--profile telegram` to run the direct Telegram bot. Install OpenClaw per official docs alongside this stack; keep the learning API on a private Docker network and only expose 443 via a reverse proxy if needed.
