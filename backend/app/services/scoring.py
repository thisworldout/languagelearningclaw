"""CEFR estimation from word frequency + level-aware ranking."""

from __future__ import annotations

from wordfreq import zipf_frequency

from app.models import CEFRLevel

LEVEL_ORDER: list[str] = [e.value for e in CEFRLevel]


def level_to_index(level: str) -> int:
    lv = level.upper().strip()
    if lv in LEVEL_ORDER:
        return LEVEL_ORDER.index(lv)
    return 2  # default A2


def zipf_to_cefr(zipf: float) -> str:
    """Rough mapping English zipf → CEFR band (heuristic)."""
    if zipf < 3.2:
        return CEFRLevel.A0.value
    if zipf < 3.7:
        return CEFRLevel.A1.value
    if zipf < 4.1:
        return CEFRLevel.A2.value
    if zipf < 4.5:
        return CEFRLevel.B1.value
    return CEFRLevel.B2.value


def lemma_zipf(lemma: str, lang: str = "en") -> float:
    z = zipf_frequency(lemma, lang, wordlist="best")
    return float(z)


def score_candidate(
    lemma: str,
    estimated_cefr: str,
    user_level: str,
    times_known: int,
    lang: str = "en",
) -> tuple[float, list[str]]:
    """
    Higher = better pick for study. Penalize too-easy (already mastered) and far-too-hard.
    """
    tags: list[str] = []
    uz = level_to_index(user_level)
    ez = level_to_index(estimated_cefr)
    diff = ez - uz

    # Base: prefer words near user's level (slight stretch ok)
    base = 10.0 - abs(min(diff, 3)) * 1.8
    if diff == 1:
        base += 2.0
        tags.append("stretch")
    if diff == 0:
        tags.append("at_level")
    if diff < 0:
        base -= 1.5
        tags.append("below_level")
    if diff > 2:
        base -= 4.0
        tags.append("too_hard")

    # Repetition: words seen many times without mastery get boost
    if times_known > 0:
        base += min(times_known * 0.4, 2.0)
        tags.append("review")

    z = lemma_zipf(lemma, lang)
    # Mid-frequency often most useful
    if 3.5 <= z <= 5.0:
        base += 0.5
        tags.append("useful_freq")

    return base, tags
