from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, verify_integration_key
from app.db.session import get_db
from app.models.usage import TTSUsageLog
from app.schemas.common import ListResponse
from app.schemas.usage import TTSLogCreate, TTSLogOut


router = APIRouter(prefix="/tts-logs", tags=["tts-logs"])
integration_router = APIRouter(prefix="/integration/tts-logs", tags=["integration"])


@router.get("", response_model=ListResponse[TTSLogOut], dependencies=[Depends(get_current_admin)])
def list_tts_logs(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user_id: int | None = None,
    provider: str = "",
    language: str = "",
    request_type: str = "",
    success: bool | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict:
    stmt = select(TTSUsageLog)
    count_stmt = select(func.count()).select_from(TTSUsageLog)
    conditions = []
    if user_id is not None:
        conditions.append(TTSUsageLog.user_id == user_id)
    if provider:
        conditions.append(TTSUsageLog.provider == provider)
    if language:
        conditions.append(TTSUsageLog.language == language)
    if request_type:
        conditions.append(TTSUsageLog.request_type == request_type)
    if success is not None:
        conditions.append(TTSUsageLog.success == success)
    if start_at:
        conditions.append(TTSUsageLog.created_at >= start_at)
    if end_at:
        conditions.append(TTSUsageLog.created_at <= end_at)
    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    stmt = stmt.order_by(TTSUsageLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    return {
        "data": db.execute(stmt).scalars().all(),
        "total": db.execute(count_stmt).scalar_one(),
    }


@router.get("/{log_id}", response_model=TTSLogOut, dependencies=[Depends(get_current_admin)])
def get_tts_log(log_id: int, db: Session = Depends(get_db)) -> TTSUsageLog:
    log = db.get(TTSUsageLog, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")
    return log


@integration_router.post("", response_model=TTSLogOut, status_code=status.HTTP_201_CREATED)
def create_tts_log(
    payload: TTSLogCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> TTSUsageLog:
    log = TTSUsageLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
