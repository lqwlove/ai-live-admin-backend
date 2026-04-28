from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LiveSessionOut(BaseModel):
    id: int
    user_id: int | None = None
    platform: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    messages_count: int
    ai_replies_count: int
    audio_played_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiveSessionStart(BaseModel):
    user_id: int | None = None
    platform: str = ""


class LiveSessionFinish(BaseModel):
    status: str = "finished"
    messages_count: int = Field(default=0, ge=0)
    ai_replies_count: int = Field(default=0, ge=0)
    audio_played_count: int = Field(default=0, ge=0)


class AITokenLogCreate(BaseModel):
    user_id: int | None = None
    session_id: int | None = None
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    request_type: str = ""
    success: bool = True
    error_message: str | None = None
    raw_usage: dict[str, Any] | None = None


class AITokenLogOut(AITokenLogCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TTSLogCreate(BaseModel):
    user_id: int | None = None
    session_id: int | None = None
    provider: str = ""
    voice: str = ""
    language: str = ""
    text_chars: int = Field(default=0, ge=0)
    audio_path: str = ""
    duration_ms: int = Field(default=0, ge=0)
    cache_hit: bool = False
    request_type: str = ""
    success: bool = True
    error_message: str | None = None
    raw_usage: dict[str, Any] | None = None


class TTSLogOut(TTSLogCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    users_total: int
    users_active: int
    users_disabled: int
    ai_tokens_today: int
    tts_chars_today: int
    ai_failures_today: int
    tts_failures_today: int
