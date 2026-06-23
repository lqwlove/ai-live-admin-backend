from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AppSetting(Base, TimestampMixin):
    """通用键值配置表。

    用于存放后台可配置项（如 AI / 语音合成的 api_key 等），
    key 形如 "ai.api_key" / "tts.api_key"，value 为字符串。
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
