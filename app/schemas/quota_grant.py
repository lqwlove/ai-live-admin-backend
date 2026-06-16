from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


QuotaKind = Literal["ai_token", "tts_chars"]


def _validate_multiplier(value: Decimal | float | str) -> Decimal:
    dec = Decimal(str(value))
    if dec < Decimal("0.1") or dec > Decimal("99.9"):
        raise ValueError("消耗倍率须在 0.1 到 99.9 之间")
    if dec != dec.quantize(Decimal("0.1")):
        raise ValueError("消耗倍率最多保留 1 位小数")
    return dec


class QuotaGrantCreate(BaseModel):
    user_id: int
    kind: QuotaKind
    amount: int = Field(gt=0, description="本次开通的额度数量（计费单位），必须为正数")
    multiplier: Decimal = Field(default=Decimal("1.0"), description="该包消耗倍率")
    note: str | None = Field(default=None, max_length=255)

    @field_validator("multiplier", mode="before")
    @classmethod
    def validate_multiplier(cls, value: Decimal | float | str) -> Decimal:
        return _validate_multiplier(value)


class QuotaGrantOut(BaseModel):
    id: int
    user_id: int
    user_username: str | None = None
    kind: str
    amount: int
    consumed: int = 0
    remaining: int = 0
    multiplier: Decimal
    note: str | None = None
    operator_id: int | None = None
    operator_username: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
