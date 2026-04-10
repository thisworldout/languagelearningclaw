"""ElevenLabs text-to-speech."""

from __future__ import annotations

import base64

import httpx

from app.config import get_settings


def build_lesson_script(word_lemmas: list[str], target_language: str) -> str:
    words = ", ".join(word_lemmas[:12])
    return (
        f"Today's focus words in {target_language}: {words}. "
        "Listen and repeat each word twice in your mind."
    )


async def synthesize_voice(text: str) -> tuple[bytes, str]:
    settings = get_settings()
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise RuntimeError("ElevenLabs not configured (ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID)")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
    payload = {
        "text": text[:2500],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.content, "audio/mpeg"
