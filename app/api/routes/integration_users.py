from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import verify_integration_key
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import AppUsageOut
from app.services.quota import get_user_usage

router = APIRouter(prefix="/integration/users", tags=["integration"])


@router.get("/{user_id}/usage", response_model=AppUsageOut)
def integration_user_usage(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> AppUsageOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    summary = get_user_usage(db, user)
    return AppUsageOut(
        ai_token_limit=summary.ai_token_limit,
        tts_chars_limit=summary.tts_chars_limit,
        consumption_multiplier=summary.consumption_multiplier,
        ai_token_used=summary.ai_token_used,
        tts_chars_used=summary.tts_chars_used,
        ai_token_remaining=summary.ai_token_remaining,
        tts_chars_remaining=summary.tts_chars_remaining,
        ai_quota_exceeded=summary.ai_quota_exceeded,
        tts_quota_exceeded=summary.tts_quota_exceeded,
    )
