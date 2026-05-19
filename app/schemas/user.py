from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_multiplier(value: Decimal | float | str) -> Decimal:
    dec = Decimal(str(value))
    if dec < Decimal("0.1") or dec > Decimal("99.9"):
        raise ValueError("消耗倍率须在 0.1 到 99.9 之间")
    if dec != dec.quantize(Decimal("0.1")):
        raise ValueError("消耗倍率最多保留 1 位小数")
    return dec


class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    role: str = "user"
    status: str = "active"
    ai_token_limit: int | None = Field(default=None, ge=0)
    tts_chars_limit: int | None = Field(default=None, ge=0)
    consumption_multiplier: Decimal = Field(default=Decimal("1.0"))

    @field_validator("consumption_multiplier", mode="before")
    @classmethod
    def validate_multiplier(cls, value: Decimal | float | str) -> Decimal:
        return _validate_multiplier(value)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=64)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: str | None = None
    status: str | None = None
    ai_token_limit: int | None = Field(default=None, ge=0)
    tts_chars_limit: int | None = Field(default=None, ge=0)
    consumption_multiplier: Decimal | None = None

    @field_validator("consumption_multiplier", mode="before")
    @classmethod
    def validate_multiplier(cls, value: Decimal | float | str | None) -> Decimal | None:
        if value is None:
            return None
        return _validate_multiplier(value)


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
    ai_token_used: int | None = None
    tts_chars_used: int | None = None

    model_config = ConfigDict(from_attributes=True)


class AppUsageOut(BaseModel):
    ai_token_limit: int | None = None
    tts_chars_limit: int | None = None
    consumption_multiplier: Decimal
    ai_token_used: int
    tts_chars_used: int
    ai_token_remaining: int | None = None
    tts_chars_remaining: int | None = None
    ai_quota_exceeded: bool
    tts_quota_exceeded: bool
