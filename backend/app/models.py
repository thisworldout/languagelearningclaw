from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CEFRLevel(str, enum.Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profiles: Mapped[list[LanguageProfile]] = relationship(back_populates="user")
    sentences: Mapped[list[SubmittedSentence]] = relationship(back_populates="user")
    vocab_progress: Mapped[list[UserVocabProgress]] = relationship(back_populates="user")
    review_events: Mapped[list[ReviewEvent]] = relationship(back_populates="user")
    weekly_plans: Mapped[list[WeeklyPlan]] = relationship(back_populates="user")


class LanguageProfile(Base):
    __tablename__ = "language_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target_language: Mapped[str] = mapped_column(String(16), default="en")
    native_language: Mapped[str] = mapped_column(String(16), default="en")
    level: Mapped[str] = mapped_column(
        String(8), default=CEFRLevel.A2.value
    )  # store as string for simplicity
    prefs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="profiles")

    __table_args__ = (UniqueConstraint("user_id", "target_language", name="uq_user_target_lang"),)


class SubmittedSentence(Base):
    __tablename__ = "submitted_sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="en")
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="sentences")


class VocabItem(Base):
    __tablename__ = "vocab_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lemma: Mapped[str] = mapped_column(String(128), index=True)
    language: Mapped[str] = mapped_column(String(16), index=True)
    cefr_estimate: Mapped[str | None] = mapped_column(String(8), nullable=True)
    frequency_zipf: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (UniqueConstraint("lemma", "language", name="uq_lemma_lang"),)


class UserVocabProgress(Base):
    __tablename__ = "user_vocab_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vocab_item_id: Mapped[int] = mapped_column(ForeignKey("vocab_items.id"), index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    times_encountered: Mapped[int] = mapped_column(Integer, default=1)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_seen_sentence_id: Mapped[int | None] = mapped_column(
        ForeignKey("submitted_sentences.id"), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="vocab_progress")
    vocab_item: Mapped[VocabItem] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "vocab_item_id", name="uq_user_vocab"),)


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vocab_item_id: Mapped[int] = mapped_column(ForeignKey("vocab_items.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32))
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="review_events")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="weekly_plans")

    __table_args__ = (UniqueConstraint("user_id", "week_start", name="uq_user_week"),)
