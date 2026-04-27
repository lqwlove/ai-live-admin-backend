from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.usage import AITokenUsageLog, TTSUsageLog
from app.models.user import User
from app.schemas.usage import DashboardSummary


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

    users_total = db.execute(select(func.count()).select_from(User)).scalar_one()
    users_active = db.execute(
        select(func.count()).select_from(User).where(User.status == "active")
    ).scalar_one()
    users_disabled = db.execute(
        select(func.count()).select_from(User).where(User.status == "disabled")
    ).scalar_one()
    ai_tokens_today = db.execute(
        select(func.coalesce(func.sum(AITokenUsageLog.total_tokens), 0)).where(
            AITokenUsageLog.created_at >= today_start
        )
    ).scalar_one()
    tts_chars_today = db.execute(
        select(func.coalesce(func.sum(TTSUsageLog.text_chars), 0)).where(
            TTSUsageLog.created_at >= today_start
        )
    ).scalar_one()
    ai_failures_today = db.execute(
        select(func.count()).select_from(AITokenUsageLog).where(
            AITokenUsageLog.created_at >= today_start,
            AITokenUsageLog.success.is_(False),
        )
    ).scalar_one()
    tts_failures_today = db.execute(
        select(func.count()).select_from(TTSUsageLog).where(
            TTSUsageLog.created_at >= today_start,
            TTSUsageLog.success.is_(False),
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
