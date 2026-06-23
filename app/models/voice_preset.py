from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class VoicePreset(Base, TimestampMixin):
    """按用户隔离的语音合成音色列表。

    每条记录是一个音色（speaker_id）与其资源 ID（resource_id）的一对一配置，
    同一用户可配置多条。客户端按当前用户拉取该列表，替代写死的 VOLCENGINE_VOICES。
    """

    __tablename__ = "voice_presets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    voice_id: Mapped[str] = mapped_column(String(128))  # speaker_id，传给火山 API 的实际值
    name: Mapped[str] = mapped_column(String(128), default="")  # 显示名称
    lang: Mapped[str] = mapped_column(String(64), default="")  # 擅长语言（仅展示用）
    resource_id: Mapped[str] = mapped_column(String(64), default="")  # 火山资源 ID
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
