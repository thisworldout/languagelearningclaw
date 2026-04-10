#!/usr/bin/env python3
"""
Minimal Telegram bot: forwards text and voice to the learning backend.
Configure: TELEGRAM_BOT_TOKEN, LEARNING_API_BASE, LEARNING_API_KEY
"""

from __future__ import annotations

import logging
import os

import httpx
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = os.environ.get("LEARNING_API_BASE", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.environ.get("LEARNING_API_KEY", "dev-insecure-change-me")


async def call_analyze(telegram_user_id: int, sentence: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{API_BASE}/v1/analyze-sentence",
            headers={"X-API-Key": API_KEY},
            json={
                "telegram_user_id": telegram_user_id,
                "sentence": sentence,
                "language": "en",
            },
        )
        r.raise_for_status()
        data = r.json()
    return data.get("explanation_markdown", str(data))


async def call_transcribe(data: bytes, filename: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{API_BASE}/v1/transcribe",
            headers={"X-API-Key": API_KEY},
            files={"file": (filename, data, "application/octet-stream")},
            data={"language_hint": "en"},
        )
        r.raise_for_status()
        return r.json().get("text", "")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id if update.effective_user else 0
    try:
        reply = await call_analyze(uid, update.message.text)
        await update.message.reply_text(reply[:4000])
    except Exception as e:
        logger.exception("analyze failed")
        await update.message.reply_text(f"Sorry, something went wrong: {e}")


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return
    uid = update.effective_user.id if update.effective_user else 0
    try:
        assert context.bot
        vf = await context.bot.get_file(update.message.voice.file_id)
        buf = await vf.download_as_bytearray()
        text = await call_transcribe(bytes(buf), "voice.ogg")
        if not text.strip():
            await update.message.reply_text("Could not transcribe audio.")
            return
        await update.message.reply_text(f"_Heard:_ {text}", parse_mode="Markdown")
        reply = await call_analyze(uid, text)
        await update.message.reply_text(reply[:4000])
    except Exception as e:
        logger.exception("voice failed")
        await update.message.reply_text(f"Sorry, something went wrong: {e}")


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    logger.info("Starting polling…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
