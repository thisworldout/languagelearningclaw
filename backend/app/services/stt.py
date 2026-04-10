"""Speech-to-text via OpenAI-compatible Whisper endpoint."""

from __future__ import annotations

import io

import httpx

from app.config import get_settings


async def transcribe_audio_bytes(data: bytes, filename: str, language: str | None) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key required for transcription")

    url = f"{settings.openai_base_url.rstrip('/')}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    files = {
        "file": (filename, io.BytesIO(data), "application/octet-stream"),
    }
    data_form = {"model": settings.whisper_model}
    if language:
        data_form["language"] = language[:2]

    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, data=data_form, files=files)
        r.raise_for_status()
        out = r.json()
    return (out.get("text") or "").strip()
