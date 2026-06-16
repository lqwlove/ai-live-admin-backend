from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class QuotaGrant(Base, TimestampMixin):
    """一个独立额度包（开通即一个包，含独立余额与倍率）。

    - amount   : 包的总额度（计费单位）
    - consumed : 已消耗（计费单位），remaining = amount - consumed
    - multiplier: 该包的消耗倍率，实际扣减 = 原始消耗 × multiplier（向上取整）
    消耗时按开通顺序（id 升序）先用先扣，一次消耗可跨多个包分段扣减。
    """

    __tablename__ = "quota_grants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # ai_token | tts_chars
    kind: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    consumed: Mapped[int] = mapped_column(BigInteger, default=0)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=Decimal("1.0"))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    operator_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="quota_grants")
    operator = relationship("User", foreign_keys=[operator_id])

    @property
    def remaining(self) -> int:
        return max(0, int(self.amount) - int(self.consumed or 0))
