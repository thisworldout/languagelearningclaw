from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.deps import verify_api_key
from app.db import get_db
from app.schemas import TranscribeResponse
from app.services.stt import transcribe_audio_bytes

router = APIRouter(prefix="/v1", tags=["transcribe"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    file: UploadFile = File(...),
    language_hint: str | None = Form(default=None),
) -> TranscribeResponse:
    _ = db
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    try:
        text = await transcribe_audio_bytes(data, file.filename or "audio.ogg", language_hint)
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    return TranscribeResponse(text=text)
