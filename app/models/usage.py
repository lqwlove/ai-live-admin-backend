from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AITokenUsageLog(Base, TimestampMixin):
    __tablename__ = "ai_token_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("live_sessions.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), default="", index=True)
    model: Mapped[str] = mapped_column(String(128), default="", index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    request_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="ai_token_logs")
    session = relationship("LiveSession", back_populates="ai_token_logs")


class TTSUsageLog(Base, TimestampMixin):
    __tablename__ = "tts_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("live_sessions.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), default="", index=True)
    voice: Mapped[str] = mapped_column(String(128), default="", index=True)
    language: Mapped[str] = mapped_column(String(32), default="", index=True)
    text_chars: Mapped[int] = mapped_column(Integer, default=0)
    audio_path: Mapped[str] = mapped_column(String(512), default="")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    request_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="tts_logs")
    session = relationship("LiveSession", back_populates="tts_logs")
