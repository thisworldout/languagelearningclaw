"""OpenAI-compatible chat for explanations."""

from __future__ import annotations

import json

import httpx

from app.config import get_settings
from app.schemas import WordCandidate


async def format_explanation(
    sentence: str,
    user_level: str,
    words: list[WordCandidate],
) -> tuple[str, bool]:
    settings = get_settings()
    if not settings.openai_api_key or not words:
        return _fallback_markdown(sentence, user_level, words), False

    payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a language tutor. Given a sentence and a list of lemmas to study, "
                    "write a concise Markdown reply: short intro, then for each word: "
                    "**lemma** — meaning in simple English, one example sentence (can be new). "
                    "Note if the word is at level, stretch, or review. Keep under 400 words."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "sentence": sentence,
                        "learner_level": user_level,
                        "words": [w.model_dump() for w in words],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
    text = data["choices"][0]["message"]["content"].strip()
    return text, True


def _fallback_markdown(sentence: str, user_level: str, words: list[WordCandidate]) -> str:
    lines = [
        f"Here is what stands out in your sentence (level **{user_level}**):",
        "",
    ]
    for w in words:
        lines.append(
            f"- **{w.lemma}** — estimated **{w.estimated_cefr}** "
            f"({' / '.join(w.reason_tags) or 'general'})."
        )
    lines.extend(["", f"_Original sentence:_ {sentence}"])
    return "\n".join(lines)
