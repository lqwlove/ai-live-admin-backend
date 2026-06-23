from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, verify_integration_key
from app.db.session import get_db
from app.models.live_session import LiveSession
from app.models.user import User
from app.schemas.common import ListResponse
from app.schemas.usage import LiveSessionFinish, LiveSessionOut, LiveSessionStart


router = APIRouter(prefix="/live-sessions", tags=["live-sessions"])
integration_router = APIRouter(prefix="/integration/live-sessions", tags=["integration"])


def _session_out(session: LiveSession) -> LiveSessionOut:
    out = LiveSessionOut.model_validate(session)
    if session.user is not None:
        out.user_username = session.user.username
    return out


@router.get("", response_model=ListResponse[LiveSessionOut])
def list_live_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user_id: int | None = None,
    platform: str = "",
    status_: str = Query(default="", alias="status"),
    sort: str = "id",
    order: str = "desc",
) -> dict:
    # 非管理员只能查看自己的开播记录
    if current_user.role != "admin":
        user_id = current_user.id

    stmt = select(LiveSession)
    count_stmt = select(func.count()).select_from(LiveSession)
    conditions = []
    if user_id is not None:
        conditions.append(LiveSession.user_id == user_id)
    if platform:
        conditions.append(LiveSession.platform == platform)
    if status_:
        conditions.append(LiveSession.status == status_)
    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    sort_column = getattr(LiveSession, sort, LiveSession.id)
    if order.lower() == "desc":
        sort_column = sort_column.desc()
    stmt = stmt.order_by(sort_column).offset((page - 1) * per_page).limit(per_page)

    sessions = db.execute(stmt).scalars().all()
    total = db.execute(count_stmt).scalar_one()
    return {
        "data": [_session_out(s) for s in sessions],
        "total": total,
    }


@router.get("/{session_id}", response_model=LiveSessionOut)
def get_live_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LiveSessionOut:
    session = db.get(LiveSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场次不存在")
    if current_user.role != "admin" and session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场次不存在")
    return _session_out(session)


@integration_router.post("", response_model=LiveSessionOut, status_code=status.HTTP_201_CREATED)
def start_live_session(
    payload: LiveSessionStart,
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> LiveSession:
    session = LiveSession(
        user_id=payload.user_id,
        platform=payload.platform,
        room_id=payload.room_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@integration_router.post("/{session_id}/finish", response_model=LiveSessionOut)
def finish_live_session(
    session_id: int,
    payload: LiveSessionFinish,
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> LiveSession:
    session = db.get(LiveSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场次不存在")

    session.status = payload.status
    session.ended_at = datetime.now(timezone.utc)
    session.messages_count = payload.messages_count
    session.ai_replies_count = payload.ai_replies_count
    session.audio_played_count = payload.audio_played_count
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
