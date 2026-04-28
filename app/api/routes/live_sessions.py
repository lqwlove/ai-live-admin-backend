from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import verify_integration_key
from app.db.session import get_db
from app.models.live_session import LiveSession
from app.schemas.usage import LiveSessionFinish, LiveSessionOut, LiveSessionStart


integration_router = APIRouter(prefix="/integration/live-sessions", tags=["integration"])


@integration_router.post("", response_model=LiveSessionOut, status_code=status.HTTP_201_CREATED)
def start_live_session(
    payload: LiveSessionStart,
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> LiveSession:
    session = LiveSession(
        user_id=payload.user_id,
        platform=payload.platform,
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
