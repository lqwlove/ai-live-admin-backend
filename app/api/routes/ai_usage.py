from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, verify_integration_key
from app.db.session import get_db
from app.models.usage import AITokenUsageLog
from app.schemas.common import ListResponse
from app.schemas.usage import AITokenLogCreate, AITokenLogOut


router = APIRouter(prefix="/ai-token-logs", tags=["ai-token-logs"])
integration_router = APIRouter(prefix="/integration/ai-token-logs", tags=["integration"])


@router.get("", response_model=ListResponse[AITokenLogOut], dependencies=[Depends(get_current_admin)])
def list_ai_token_logs(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user_id: int | None = None,
    model: str = "",
    provider: str = "",
    success: bool | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict:
    stmt = select(AITokenUsageLog)
    count_stmt = select(func.count()).select_from(AITokenUsageLog)
    conditions = []
    if user_id is not None:
        conditions.append(AITokenUsageLog.user_id == user_id)
    if model:
        conditions.append(AITokenUsageLog.model == model)
    if provider:
        conditions.append(AITokenUsageLog.provider == provider)
    if success is not None:
        conditions.append(AITokenUsageLog.success == success)
    if start_at:
        conditions.append(AITokenUsageLog.created_at >= start_at)
    if end_at:
        conditions.append(AITokenUsageLog.created_at <= end_at)
    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    stmt = (
        stmt.order_by(AITokenUsageLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return {
        "data": db.execute(stmt).scalars().all(),
        "total": db.execute(count_stmt).scalar_one(),
    }


@router.get("/{log_id}", response_model=AITokenLogOut, dependencies=[Depends(get_current_admin)])
def get_ai_token_log(log_id: int, db: Session = Depends(get_db)) -> AITokenUsageLog:
    log = db.get(AITokenUsageLog, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")
    return log


@integration_router.post("", response_model=AITokenLogOut, status_code=status.HTTP_201_CREATED)
def create_ai_token_log(
    payload: AITokenLogCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> AITokenUsageLog:
    log = AITokenUsageLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
