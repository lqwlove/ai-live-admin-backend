from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class LiveSession(Base, TimestampMixin):
    __tablename__ = "live_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    platform: Mapped[str] = mapped_column(String(64), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_replies_count: Mapped[int] = mapped_column(Integer, default=0)
    audio_played_count: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="live_sessions")
    ai_token_logs = relationship("AITokenUsageLog", back_populates="session")
    tts_logs = relationship("TTSUsageLog", back_populates="session")
