import base64

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import verify_api_key
from app.db import get_db
from app.schemas import GenerateAudioRequest, GenerateAudioResponse
from app.services.tts import build_lesson_script, synthesize_voice

router = APIRouter(prefix="/v1", tags=["audio"])


@router.post("/generate-audio", response_model=GenerateAudioResponse)
async def generate_audio(
    body: GenerateAudioRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> GenerateAudioResponse:
    _ = db  # reserved for future user-specific scripts
    if body.lesson_script:
        script = body.lesson_script
    elif body.word_lemmas:
        script = build_lesson_script(body.word_lemmas, body.target_language)
    else:
        raise HTTPException(400, "Provide lesson_script or word_lemmas")
    try:
        raw, mime = await synthesize_voice(script)
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    return GenerateAudioResponse(
        mime_type=mime,
        base64_audio=base64.standard_b64encode(raw).decode("ascii"),
        duration_hint_sec=None,
    )
