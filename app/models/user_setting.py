from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserSetting(Base, TimestampMixin):
    """按用户隔离的键值配置表。

    用于存放每个用户自己的后台可配置项（如 AI / 语音合成的 api_key 等），
    key 形如 "ai.api_key" / "tts.api_key"，value 为字符串。
    主键为 (user_id, key)。
    """

    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
