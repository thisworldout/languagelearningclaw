"""Rule-based weekly summary with optional LLM polish."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ReviewEvent, User, UserVocabProgress, VocabItem, WeeklyPlan
from app.schemas import WeeklySummaryResponse


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def build_weekly_summary(db: Session, telegram_user_id: int) -> WeeklySummaryResponse:
    user = db.execute(select(User).where(User.telegram_user_id == telegram_user_id)).scalar_one_or_none()
    if not user:
        user = User(telegram_user_id=telegram_user_id)
        db.add(user)
        db.flush()

    start = _week_start(date.today())
    end = start + timedelta(days=7)
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.min)

    n_review = db.execute(
        select(func.count(ReviewEvent.id)).where(
            ReviewEvent.user_id == user.id,
            ReviewEvent.created_at >= start_dt,
            ReviewEvent.created_at < end_dt,
        )
    ).scalar() or 0

    weak_rows = db.execute(
        select(VocabItem.lemma, UserVocabProgress.mastery_score)
        .join(VocabItem, VocabItem.id == UserVocabProgress.vocab_item_id)
        .where(
            UserVocabProgress.user_id == user.id,
            UserVocabProgress.mastery_score < 0.5,
        )
        .order_by(UserVocabProgress.mastery_score.asc())
        .limit(8)
    ).all()
    weak_sample = [r[0] for r in weak_rows]

    new_words = db.execute(
        select(func.count(UserVocabProgress.id)).where(
            UserVocabProgress.user_id == user.id,
            UserVocabProgress.first_seen >= start_dt,
            UserVocabProgress.first_seen < end_dt,
        )
    ).scalar() or 0

    base_md = "\n".join(
        [
            f"**Week of {start}**",
            "",
            f"- New words tracked this week: **{new_words}**",
            f"- Review events: **{n_review}**",
            f"- Words still weak (sample): {', '.join(weak_sample) or '—'}",
            "",
            "Keep reviewing weak items; send a new sentence anytime.",
        ]
    )

    polished = await _maybe_polish_markdown(base_md)
    content = {
        "new_words_count": new_words,
        "review_events_count": n_review,
        "weak_words_sample": weak_sample,
        "raw_markdown": base_md,
    }
    wp = db.execute(
        select(WeeklyPlan).where(WeeklyPlan.user_id == user.id, WeeklyPlan.week_start == start)
    ).scalar_one_or_none()
    if wp:
        wp.content = content
    else:
        wp = WeeklyPlan(user_id=user.id, week_start=start, content=content)
        db.add(wp)
    db.commit()

    return WeeklySummaryResponse(
        week_start=start,
        new_words_count=new_words,
        weak_words_sample=weak_sample,
        review_events_count=n_review,
        summary_markdown=polished,
    )


async def _maybe_polish_markdown(text: str) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        return text
    payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": "Rewrite the following weekly study summary in friendly Markdown. Keep facts identical.",
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        if r.status_code >= 400:
            return text
        data = r.json()
    return data["choices"][0]["message"]["content"].strip()
