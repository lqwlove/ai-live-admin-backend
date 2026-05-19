import math
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.usage import AITokenUsageLog, TTSUsageLog
from app.models.user import User


class QuotaExceededError(Exception):
    def __init__(
        self,
        kind: str,
        *,
        used: int,
        limit: int,
        multiplier: Decimal,
        delta: int = 0,
    ) -> None:
        self.kind = kind
        self.used = used
        self.limit = limit
        self.multiplier = multiplier
        self.delta = delta
        super().__init__(f"{kind} quota exceeded")

    def to_detail(self) -> dict:
        return {
            "code": "quota_exceeded",
            "kind": self.kind,
            "used": self.used,
            "limit": self.limit,
            "multiplier": float(self.multiplier),
            "delta": self.delta,
        }


@dataclass
class UserUsageSummary:
    ai_token_limit: int | None
    tts_chars_limit: int | None
    consumption_multiplier: Decimal
    ai_token_used: int
    tts_chars_used: int

    @property
    def ai_token_remaining(self) -> int | None:
        if self.ai_token_limit is None:
            return None
        return max(0, self.ai_token_limit - self.ai_token_used)

    @property
    def tts_chars_remaining(self) -> int | None:
        if self.tts_chars_limit is None:
            return None
        return max(0, self.tts_chars_limit - self.tts_chars_used)

    @property
    def ai_quota_exceeded(self) -> bool:
        if self.ai_token_limit is None:
            return False
        return self.ai_token_used >= self.ai_token_limit

    @property
    def tts_quota_exceeded(self) -> bool:
        if self.tts_chars_limit is None:
            return False
        return self.tts_chars_used >= self.tts_chars_limit


def apply_multiplier(raw: int, multiplier: Decimal) -> int:
    if raw <= 0:
        return 0
    return int(math.ceil(raw * float(multiplier)))


def get_user_multiplier(user: User) -> Decimal:
    return Decimal(str(user.consumption_multiplier or "1.0"))


def is_quota_exempt(user: User) -> bool:
    return user.role == "admin"


def get_user_usage(db: Session, user: User) -> UserUsageSummary:
    ai_used = 0
    tts_used = 0
    if user.id is not None:
        ai_used = db.execute(
            select(func.coalesce(func.sum(AITokenUsageLog.billed_units), 0)).where(
                AITokenUsageLog.user_id == user.id,
                AITokenUsageLog.success.is_(True),
            )
        ).scalar_one()
        tts_used = db.execute(
            select(func.coalesce(func.sum(TTSUsageLog.billed_units), 0)).where(
                TTSUsageLog.user_id == user.id,
                TTSUsageLog.success.is_(True),
            )
        ).scalar_one()
    return UserUsageSummary(
        ai_token_limit=user.ai_token_limit,
        tts_chars_limit=user.tts_chars_limit,
        consumption_multiplier=get_user_multiplier(user),
        ai_token_used=int(ai_used),
        tts_chars_used=int(tts_used),
    )


def check_quota(
    user: User,
    usage: UserUsageSummary,
    *,
    ai_delta: int = 0,
    tts_delta: int = 0,
) -> None:
    if is_quota_exempt(user):
        return

    multiplier = usage.consumption_multiplier

    if user.ai_token_limit is not None and ai_delta > 0:
        next_ai = usage.ai_token_used + ai_delta
        if next_ai > user.ai_token_limit:
            raise QuotaExceededError(
                "ai_token",
                used=usage.ai_token_used,
                limit=user.ai_token_limit,
                multiplier=multiplier,
                delta=ai_delta,
            )

    if user.tts_chars_limit is not None and tts_delta > 0:
        next_tts = usage.tts_chars_used + tts_delta
        if next_tts > user.tts_chars_limit:
            raise QuotaExceededError(
                "tts_chars",
                used=usage.tts_chars_used,
                limit=user.tts_chars_limit,
                multiplier=multiplier,
                delta=tts_delta,
            )


def lock_user_for_quota(db: Session, user_id: int) -> User | None:
    return db.execute(select(User).where(User.id == user_id).with_for_update()).scalar_one_or_none()
