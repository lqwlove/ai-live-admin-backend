from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    role: str = "user"
    status: str = "active"


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=64)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: str | None = None
    status: str | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    # 由额度包聚合得到（只读）。这些字段会读到用户表里已废弃且可能为 NULL 的旧列，
    # 因此统一把 None 归一为 0。
    ai_token_limit: int = 0
    tts_chars_limit: int = 0
    ai_token_used: int = 0
    tts_chars_used: int = 0
    ai_token_remaining: int = 0
    tts_chars_remaining: int = 0

    @field_validator(
        "ai_token_limit",
        "tts_chars_limit",
        "ai_token_used",
        "tts_chars_used",
        "ai_token_remaining",
        "tts_chars_remaining",
        mode="before",
    )
    @classmethod
    def _none_to_zero(cls, value: int | None) -> int:
        return 0 if value is None else value

    model_config = ConfigDict(from_attributes=True)


class AppUsageOut(BaseModel):
    ai_token_limit: int = 0
    tts_chars_limit: int = 0
    consumption_multiplier: Decimal = Decimal("1.0")
    ai_token_used: int = 0
    tts_chars_used: int = 0
    ai_token_remaining: int = 0
    tts_chars_remaining: int = 0
    ai_quota_exceeded: bool = False
    tts_quota_exceeded: bool = False
