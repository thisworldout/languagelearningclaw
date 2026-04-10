from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class WordCandidate(BaseModel):
    lemma: str
    surface_forms: list[str] = Field(default_factory=list)
    estimated_cefr: str
    zipf_score: float | None = None
    rank_score: float
    reason_tags: list[str] = Field(default_factory=list)


class AnalyzeSentenceRequest(BaseModel):
    telegram_user_id: int
    sentence: str
    language: str | None = Field(default="en", description="ISO language code for NLP")
    target_language: str | None = Field(default=None, description="Defaults to profile")


class AnalyzeSentenceResponse(BaseModel):
    user_id: int
    sentence_id: int
    level: str
    selected_words: list[WordCandidate]
    explanation_markdown: str
    llm_used: bool


class ProfileResponse(BaseModel):
    telegram_user_id: int
    target_language: str
    native_language: str
    level: str


class SetProfileRequest(BaseModel):
    telegram_user_id: int
    target_language: str = "en"
    native_language: str = "en"
    level: str = "A2"


class GenerateAudioRequest(BaseModel):
    telegram_user_id: int
    lesson_script: str | None = None
    word_lemmas: list[str] | None = None
    target_language: str = "en"


class GenerateAudioResponse(BaseModel):
    mime_type: str
    base64_audio: str
    duration_hint_sec: int | None = None


class WeeklySummaryResponse(BaseModel):
    week_start: date
    new_words_count: int
    weak_words_sample: list[str]
    review_events_count: int
    summary_markdown: str


class TranscribeRequest(BaseModel):
    telegram_user_id: int
    language_hint: str | None = "en"


class TranscribeResponse(BaseModel):
    text: str
