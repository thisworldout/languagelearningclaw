"""Orchestrates sentence analysis, persistence, and LLM explanation."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    LanguageProfile,
    ReviewEvent,
    SubmittedSentence,
    User,
    UserVocabProgress,
    VocabItem,
)
from app.schemas import AnalyzeSentenceResponse, WordCandidate
from app.services.llm import format_explanation
from app.services.nlp import tokenize_lemmas
from app.services.scoring import lemma_zipf, score_candidate, zipf_to_cefr


def _get_or_create_user(db: Session, telegram_user_id: int) -> User:
    u = db.execute(select(User).where(User.telegram_user_id == telegram_user_id)).scalar_one_or_none()
    if u:
        return u
    u = User(telegram_user_id=telegram_user_id)
    db.add(u)
    db.flush()
    return u


def _get_or_create_profile(
    db: Session, user: User, target_language: str, native_language: str, level: str
) -> LanguageProfile:
    q = select(LanguageProfile).where(
        LanguageProfile.user_id == user.id,
        LanguageProfile.target_language == target_language,
    )
    p = db.execute(q).scalar_one_or_none()
    if p:
        return p
    p = LanguageProfile(
        user_id=user.id,
        target_language=target_language,
        native_language=native_language,
        level=level,
    )
    db.add(p)
    db.flush()
    return p


def _get_or_create_vocab(db: Session, lemma: str, language: str, zipf: float, cefr: str) -> VocabItem:
    q = select(VocabItem).where(VocabItem.lemma == lemma, VocabItem.language == language)
    v = db.execute(q).scalar_one_or_none()
    if v:
        return v
    v = VocabItem(lemma=lemma, language=language, cefr_estimate=cefr, frequency_zipf=zipf)
    db.add(v)
    db.flush()
    return v


async def analyze_sentence_flow(
    db: Session,
    telegram_user_id: int,
    sentence: str,
    language: str,
    target_language: str | None,
) -> AnalyzeSentenceResponse:
    user = _get_or_create_user(db, telegram_user_id)
    tl = target_language or "en"
    profile = _get_or_create_profile(db, user, tl, native_language="en", level="A2")

    pairs = tokenize_lemmas(sentence, language)
    lemma_to_surfaces: dict[str, set[str]] = defaultdict(set)
    for lemma, surf in pairs:
        lemma_to_surfaces[lemma].add(surf)

    ranked: list[tuple[float, WordCandidate]] = []

    for lemma in lemma_to_surfaces:
        zipf = lemma_zipf(lemma, tl)
        est = zipf_to_cefr(zipf)
        vocab = _get_or_create_vocab(db, lemma, tl, zipf, est)

        uv = db.execute(
            select(UserVocabProgress).where(
                UserVocabProgress.user_id == user.id,
                UserVocabProgress.vocab_item_id == vocab.id,
            )
        ).scalar_one_or_none()
        times = uv.times_encountered if uv else 0
        mastery = uv.mastery_score if uv else 0.0

        if mastery >= 0.95:
            continue

        sc, tags = score_candidate(lemma, est, profile.level, times, lang=tl)
        if mastery > 0.7:
            sc -= 2.0
            tags.append("mostly_known")

        wc = WordCandidate(
            lemma=lemma,
            surface_forms=sorted(lemma_to_surfaces[lemma]),
            estimated_cefr=est,
            zipf_score=round(zipf, 2),
            rank_score=sc,
            reason_tags=list(dict.fromkeys(tags)),
        )
        ranked.append((sc, wc))

    ranked.sort(key=lambda x: x[0], reverse=True)
    top = [w for _, w in ranked[:8]]

    sent_row = SubmittedSentence(user_id=user.id, text=sentence, language=language, source="telegram")
    db.add(sent_row)
    db.flush()

    for wc in top:
        v = _get_or_create_vocab(db, wc.lemma, tl, wc.zipf_score or 0.0, wc.estimated_cefr)
        uv = db.execute(
            select(UserVocabProgress).where(
                UserVocabProgress.user_id == user.id,
                UserVocabProgress.vocab_item_id == v.id,
            )
        ).scalar_one_or_none()
        if uv:
            uv.times_encountered += 1
            uv.last_seen_sentence_id = sent_row.id
        else:
            uv = UserVocabProgress(
                user_id=user.id,
                vocab_item_id=v.id,
                times_encountered=1,
                last_seen_sentence_id=sent_row.id,
            )
            db.add(uv)
        db.add(
            ReviewEvent(
                user_id=user.id,
                vocab_item_id=v.id,
                event_type="encounter",
                meta={"sentence_id": sent_row.id},
            )
        )

    explanation, used_llm = await format_explanation(sentence, profile.level, top)

    db.commit()

    return AnalyzeSentenceResponse(
        user_id=user.id,
        sentence_id=sent_row.id,
        level=profile.level,
        selected_words=top,
        explanation_markdown=explanation,
        llm_used=used_llm,
    )
