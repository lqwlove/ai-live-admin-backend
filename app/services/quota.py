import math
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.quota_grant import QuotaGrant
from app.models.user import User


KIND_AI = "ai_token"
KIND_TTS = "tts_chars"


class QuotaExceededError(Exception):
    def __init__(
        self,
        kind: str,
        *,
        used: int,
        limit: int,
        remaining: int = 0,
        multiplier: Decimal = Decimal("1.0"),
        delta: int = 0,
    ) -> None:
        self.kind = kind
        self.used = used
        self.limit = limit
        self.remaining = remaining
        self.multiplier = multiplier
        self.delta = delta
        super().__init__(f"{kind} quota exceeded")

    def to_detail(self) -> dict:
        return {
            "code": "quota_exceeded",
            "kind": self.kind,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "multiplier": float(self.multiplier),
            "delta": self.delta,
        }


@dataclass
class UserUsageSummary:
    ai_token_limit: int
    tts_chars_limit: int
    ai_token_used: int
    tts_chars_used: int
    # 展示用：当前生效（FIFO 队首）包的倍率，无包时为 1.0
    consumption_multiplier: Decimal = Decimal("1.0")

    @property
    def ai_token_remaining(self) -> int:
        return max(0, self.ai_token_limit - self.ai_token_used)

    @property
    def tts_chars_remaining(self) -> int:
        return max(0, self.tts_chars_limit - self.tts_chars_used)

    @property
    def ai_quota_exceeded(self) -> bool:
        # 只有「开通过包且已用尽」才算超限，避免某类型没开通包时误把整个客户端拦死
        return self.ai_token_limit > 0 and self.ai_token_used >= self.ai_token_limit

    @property
    def tts_quota_exceeded(self) -> bool:
        return self.tts_chars_limit > 0 and self.tts_chars_used >= self.tts_chars_limit


def is_quota_exempt(user: User) -> bool:
    return user.role == "admin"


# ---------------------------------------------------------------------------
# FIFO 分段扣减（纯函数，便于单测）
# ---------------------------------------------------------------------------


@dataclass
class PackageState:
    id: int
    amount: int
    consumed: int
    multiplier: Decimal

    @property
    def remaining(self) -> int:
        return max(0, self.amount - self.consumed)


@dataclass
class ConsumePlan:
    ok: bool
    total_billed: int
    # [(package_id, billed_units)]
    deductions: list[tuple[int, int]] = field(default_factory=list)


def plan_consumption(packages: list[PackageState], raw: int) -> ConsumePlan:
    """按 FIFO 顺序把 raw 原始用量分段扣减到各包上。

    每个包的额度是「计费单位」，本包内扣减 = ceil(原始量 × 该包倍率)。
    覆盖能力 coverable = floor(remaining / multiplier)，即该包剩余还能承担多少原始量。
    若所有包都不足以覆盖剩余 raw，则返回 ok=False（不产生任何扣减）。
    """
    if raw <= 0:
        return ConsumePlan(ok=True, total_billed=0)

    raw_left = raw
    deductions: list[tuple[int, int]] = []
    total_billed = 0

    for pkg in packages:
        if raw_left <= 0:
            break
        remaining = pkg.remaining
        if remaining <= 0:
            continue
        multiplier = pkg.multiplier
        coverable = int(Decimal(remaining) // multiplier)  # 该包能承担的原始量（floor）
        if coverable <= 0:
            continue  # 剩余太少（碎屑），覆盖不了一个完整原始单位
        use_raw = min(raw_left, coverable)
        billed = int(math.ceil(Decimal(use_raw) * multiplier))
        if billed > remaining:
            billed = remaining
        deductions.append((pkg.id, billed))
        total_billed += billed
        raw_left -= use_raw

    return ConsumePlan(ok=raw_left <= 0, total_billed=total_billed, deductions=deductions)


# ---------------------------------------------------------------------------
# 用量聚合
# ---------------------------------------------------------------------------


def _head_multiplier(db: Session, user_id: int) -> Decimal:
    value = db.execute(
        select(QuotaGrant.multiplier)
        .where(
            QuotaGrant.user_id == user_id,
            QuotaGrant.consumed < QuotaGrant.amount,
        )
        .order_by(QuotaGrant.id)
        .limit(1)
    ).scalar_one_or_none()
    return Decimal(str(value)) if value is not None else Decimal("1.0")


def get_user_usage(db: Session, user: User) -> UserUsageSummary:
    totals = {KIND_AI: (0, 0), KIND_TTS: (0, 0)}
    if user.id is not None:
        rows = db.execute(
            select(
                QuotaGrant.kind,
                func.coalesce(func.sum(QuotaGrant.amount), 0),
                func.coalesce(func.sum(QuotaGrant.consumed), 0),
            )
            .where(QuotaGrant.user_id == user.id)
            .group_by(QuotaGrant.kind)
        ).all()
        for kind, amount, consumed in rows:
            totals[kind] = (int(amount), int(consumed))

    ai_limit, ai_used = totals[KIND_AI]
    tts_limit, tts_used = totals[KIND_TTS]
    multiplier = _head_multiplier(db, user.id) if user.id is not None else Decimal("1.0")
    return UserUsageSummary(
        ai_token_limit=ai_limit,
        tts_chars_limit=tts_limit,
        ai_token_used=ai_used,
        tts_chars_used=tts_used,
        consumption_multiplier=multiplier,
    )


# ---------------------------------------------------------------------------
# 消耗扣减（写入消耗日志时调用）
# ---------------------------------------------------------------------------


def lock_user_for_quota(db: Session, user_id: int) -> User | None:
    return db.execute(select(User).where(User.id == user_id).with_for_update()).scalar_one_or_none()


def consume_quota(db: Session, user: User, kind: str, raw: int) -> int:
    """按 FIFO 从用户的额度包中扣减本次原始消耗，返回计入额度的计费单位总数。

    - 管理员豁免，不扣减（返回 0）
    - raw <= 0 不扣减
    - 额度不足时抛 QuotaExceededError，且不产生任何扣减
    """
    if is_quota_exempt(user) or raw <= 0:
        return 0

    packages = (
        db.execute(
            select(QuotaGrant)
            .where(
                QuotaGrant.user_id == user.id,
                QuotaGrant.kind == kind,
                QuotaGrant.consumed < QuotaGrant.amount,
            )
            .order_by(QuotaGrant.id)
            .with_for_update()
        )
        .scalars()
        .all()
    )

    states = [
        PackageState(p.id, int(p.amount), int(p.consumed or 0), Decimal(str(p.multiplier)))
        for p in packages
    ]
    plan = plan_consumption(states, raw)

    if not plan.ok:
        summary = get_user_usage(db, user)
        if kind == KIND_AI:
            used, limit, remaining = (
                summary.ai_token_used,
                summary.ai_token_limit,
                summary.ai_token_remaining,
            )
        else:
            used, limit, remaining = (
                summary.tts_chars_used,
                summary.tts_chars_limit,
                summary.tts_chars_remaining,
            )
        raise QuotaExceededError(
            kind,
            used=used,
            limit=limit,
            remaining=remaining,
            multiplier=summary.consumption_multiplier,
            delta=raw,
        )

    by_id = {p.id: p for p in packages}
    for pkg_id, billed in plan.deductions:
        pkg = by_id[pkg_id]
        pkg.consumed = int(pkg.consumed or 0) + billed
        db.add(pkg)

    return plan.total_billed
