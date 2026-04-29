from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.usage import AITokenUsageLog, TTSUsageLog
from app.models.user import User
from app.schemas.usage import DashboardSummary


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/summary", response_model=DashboardSummary)
def summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

    if current_user.role == "admin":
        users_total = db.execute(select(func.count()).select_from(User)).scalar_one()
        users_active = db.execute(
            select(func.count()).select_from(User).where(User.status == "active")
        ).scalar_one()
        users_disabled = db.execute(
            select(func.count()).select_from(User).where(User.status == "disabled")
        ).scalar_one()
        ai_conditions = [AITokenUsageLog.created_at >= today_start]
        tts_conditions = [TTSUsageLog.created_at >= today_start]
    else:
        users_total = users_active = users_disabled = 0
        ai_conditions = [
            AITokenUsageLog.created_at >= today_start,
            AITokenUsageLog.user_id == current_user.id,
        ]
        tts_conditions = [
            TTSUsageLog.created_at >= today_start,
            TTSUsageLog.user_id == current_user.id,
        ]
    ai_tokens_today = db.execute(
        select(func.coalesce(func.sum(AITokenUsageLog.total_tokens), 0)).where(*ai_conditions)
    ).scalar_one()
    tts_chars_today = db.execute(
        select(func.coalesce(func.sum(TTSUsageLog.text_chars), 0)).where(*tts_conditions)
    ).scalar_one()
    ai_failures_today = db.execute(
        select(func.count()).select_from(AITokenUsageLog).where(
            *ai_conditions, AITokenUsageLog.success.is_(False)
        )
    ).scalar_one()
    tts_failures_today = db.execute(
        select(func.count()).select_from(TTSUsageLog).where(
            *tts_conditions, TTSUsageLog.success.is_(False)
        )
    ).scalar_one()

    return DashboardSummary(
        users_total=users_total,
        users_active=users_active,
        users_disabled=users_disabled,
        ai_tokens_today=ai_tokens_today,
        tts_chars_today=tts_chars_today,
        ai_failures_today=ai_failures_today,
        tts_failures_today=tts_failures_today,
    )
