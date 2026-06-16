from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


QuotaKind = Literal["ai_token", "tts_chars"]


class QuotaGrantCreate(BaseModel):
    user_id: int
    kind: QuotaKind
    amount: int = Field(gt=0, description="本次开通的额度数量，必须为正数")
    note: str | None = Field(default=None, max_length=255)


class QuotaGrantOut(BaseModel):
    id: int
    user_id: int
    user_username: str | None = None
    kind: str
    amount: int
    limit_after: int | None = None
    note: str | None = None
    operator_id: int | None = None
    operator_username: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
