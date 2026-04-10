from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import verify_api_key
from app.db import get_db
from app.models import LanguageProfile, User
from app.schemas import ProfileResponse, SetProfileRequest

router = APIRouter(prefix="/v1", tags=["profile"])


@router.get("/profile/{telegram_user_id}", response_model=ProfileResponse)
def get_profile(
    telegram_user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> ProfileResponse:
    user = db.execute(select(User).where(User.telegram_user_id == telegram_user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    prof = db.execute(select(LanguageProfile).where(LanguageProfile.user_id == user.id)).scalar_one_or_none()
    if not prof:
        raise HTTPException(404, "Profile not found")
    return ProfileResponse(
        telegram_user_id=telegram_user_id,
        target_language=prof.target_language,
        native_language=prof.native_language,
        level=prof.level,
    )


@router.post("/profile", response_model=ProfileResponse)
def set_profile(
    body: SetProfileRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> ProfileResponse:
    user = db.execute(select(User).where(User.telegram_user_id == body.telegram_user_id)).scalar_one_or_none()
    if not user:
        user = User(telegram_user_id=body.telegram_user_id)
        db.add(user)
        db.flush()
    prof = db.execute(
        select(LanguageProfile).where(
            LanguageProfile.user_id == user.id,
            LanguageProfile.target_language == body.target_language,
        )
    ).scalar_one_or_none()
    if prof:
        prof.native_language = body.native_language
        prof.level = body.level
    else:
        prof = LanguageProfile(
            user_id=user.id,
            target_language=body.target_language,
            native_language=body.native_language,
            level=body.level,
        )
        db.add(prof)
    db.commit()
    db.refresh(prof)
    return ProfileResponse(
        telegram_user_id=body.telegram_user_id,
        target_language=prof.target_language,
        native_language=prof.native_language,
        level=prof.level,
    )
