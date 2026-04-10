from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import verify_api_key
from app.db import get_db
from app.schemas import AnalyzeSentenceRequest, AnalyzeSentenceResponse
from app.services.analysis import analyze_sentence_flow

router = APIRouter(prefix="/v1", tags=["analyze"])


@router.post("/analyze-sentence", response_model=AnalyzeSentenceResponse)
async def analyze_sentence(
    body: AnalyzeSentenceRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> AnalyzeSentenceResponse:
    return await analyze_sentence_flow(
        db,
        body.telegram_user_id,
        body.sentence,
        body.language or "en",
        body.target_language,
    )
