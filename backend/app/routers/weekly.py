from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import verify_api_key
from app.db import get_db
from app.schemas import WeeklySummaryResponse
from app.services.weekly import build_weekly_summary

router = APIRouter(prefix="/v1", tags=["weekly"])


@router.get("/weekly-summary/{telegram_user_id}", response_model=WeeklySummaryResponse)
async def weekly_summary(
    telegram_user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> WeeklySummaryResponse:
    return await build_weekly_summary(db, telegram_user_id)
