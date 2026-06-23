from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.usage import AITokenUsageLog, TTSUsageLog
from app.models.user import User
from app.schemas.usage import DashboardSummary, UsageTrendPoint, UsageTrendResponse


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


@router.get("/usage-trend", response_model=UsageTrendResponse)
def usage_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    user_id: int | None = Query(default=None),
) -> UsageTrendResponse:
    # 默认最近 14 天（含今天）
    end_date = end or datetime.now(timezone.utc).date()
    start_date = start or (end_date - timedelta(days=13))
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)

    # 普通用户只能看自己；管理员不传 user_id 即全部用户汇总
    if current_user.role != "admin":
        target_user_id: int | None = current_user.id
    else:
        target_user_id = user_id

    def _aggregate(model, value_col) -> dict[str, int]:
        day = func.date(model.created_at)
        conditions = [model.created_at >= start_dt, model.created_at <= end_dt]
        if target_user_id is not None:
            conditions.append(model.user_id == target_user_id)
        rows = db.execute(
            select(day.label("d"), func.coalesce(func.sum(value_col), 0))
            .where(*conditions)
            .group_by(day)
        ).all()
        return {str(d): int(total or 0) for d, total in rows}

    ai_by_day = _aggregate(AITokenUsageLog, AITokenUsageLog.total_tokens)
    tts_by_day = _aggregate(TTSUsageLog, TTSUsageLog.text_chars)

    points: list[UsageTrendPoint] = []
    ai_total = 0
    tts_total = 0
    cursor = start_date
    while cursor <= end_date:
        key = cursor.isoformat()
        ai_value = ai_by_day.get(key, 0)
        tts_value = tts_by_day.get(key, 0)
        ai_total += ai_value
        tts_total += tts_value
        points.append(UsageTrendPoint(date=key, ai_tokens=ai_value, tts_chars=tts_value))
        cursor += timedelta(days=1)

    return UsageTrendResponse(
        points=points,
        ai_tokens_total=ai_total,
        tts_chars_total=tts_total,
    )
