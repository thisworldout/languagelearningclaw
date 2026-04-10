"""Tokenization and lemmatization. spaCy model loaded lazily per language."""

from __future__ import annotations

import re
from functools import lru_cache

# Default English stopwords (minimal set; spaCy also has stop words)
_EN_STOP = frozenset(
    """
    a an the and or but if in on at to from for of as by with without
    is are was were be been being have has had do does did will would could should
    it its this that these those i you he she we they me him her us them my your
    their what which who whom whose when where why how not no yes so than then
    also just only very into about up out off over such same both each few more most
    other some any all can may might must shall will
    """.split()
)


@lru_cache(maxsize=8)
def _spacy_model(name: str):
    import spacy

    return spacy.load(name)


def get_spacy_nlp(language: str):
    """Return spaCy pipeline for supported languages; fallback to English."""
    lang = (language or "en").lower()[:2]
    # MVP: ship English; other langs fall back to blank + rule lemmatizer issues — use en
    if lang != "en":
        lang = "en"
    try:
        return _spacy_model("en_core_web_sm")
    except OSError:
        raise RuntimeError(
            "spaCy model en_core_web_sm not installed. Run: python -m spacy download en_core_web_sm"
        ) from None


def tokenize_lemmas(text: str, language: str = "en") -> list[tuple[str, str]]:
    """
    Returns list of (lemma_lower, original_surface) for content words.
    Filters punctuation, numbers, and stopwords.
    """
    nlp = get_spacy_nlp(language)
    doc = nlp(text.strip())
    out: list[tuple[str, str]] = []
    for tok in doc:
        if tok.is_punct or tok.is_space or tok.like_num:
            continue
        lemma = (tok.lemma_ or tok.text).lower().strip()
        surface = tok.text.lower()
        if len(lemma) < 2 or re.match(r"^[^a-zA-ZÀ-ÖØ-öø-ÿ]+$", lemma):
            continue
        if lemma in _EN_STOP:
            continue
        out.append((lemma, surface))
    return out
