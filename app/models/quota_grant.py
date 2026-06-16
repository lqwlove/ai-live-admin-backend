from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class QuotaGrant(Base, TimestampMixin):
    """一次额度包开通记录（充值流水）。

    每次给用户开通 token 包 / 语音包都会写入一条记录，额度按 kind 累加到
    users.ai_token_limit / users.tts_chars_limit 上。
    """

    __tablename__ = "quota_grants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # ai_token | tts_chars
    kind: Mapped[str] = mapped_column(String(32), index=True)
    # 本次开通的额度数量（恒为正数）
    amount: Mapped[int] = mapped_column(BigInteger)
    # 开通后该类型的累计总额度（快照，便于审计展示）
    limit_after: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    operator_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="quota_grants")
    operator = relationship("User", foreign_keys=[operator_id])
