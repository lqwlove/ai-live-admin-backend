"""后台可配置项（AI / 语音合成 / 音色列表）的读写服务，按用户隔离。

AI / 语音合成 key 以键值对存于 user_settings 表（主键 user_id+key）。
音色列表存于 voice_presets 表，每个用户可配置多条。
未配置时回退到下方默认值（与客户端历史内置值保持一致）。
"""

from sqlalchemy.orm import Session

from app.models.user_setting import UserSetting
from app.models.voice_preset import VoicePreset
from app.schemas.settings import AIConfig, TTSConfig, VoicePresetItem

# 默认值（与 tk-live 客户端历史内置一致，作为未配置时的回退）
_DEFAULT_AI_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

AI_KEYS = {
    "api_key": "ai.api_key",
    "base_url": "ai.base_url",
    "model": "ai.model",
}
TTS_KEYS = {
    "api_key": "tts.api_key",
}


def _get_values(db: Session, user_id: int, keys: list[str]) -> dict[str, str]:
    rows = (
        db.query(UserSetting)
        .filter(UserSetting.user_id == user_id, UserSetting.key.in_(keys))
        .all()
    )
    return {row.key: row.value for row in rows}


def _set_value(db: Session, user_id: int, key: str, value: str) -> None:
    row = db.get(UserSetting, {"user_id": user_id, "key": key})
    if row is None:
        db.add(UserSetting(user_id=user_id, key=key, value=value or ""))
    else:
        row.value = value or ""


def get_ai_config(db: Session, user_id: int) -> AIConfig:
    values = _get_values(db, user_id, list(AI_KEYS.values()))
    return AIConfig(
        api_key=values.get(AI_KEYS["api_key"], ""),
        base_url=values.get(AI_KEYS["base_url"]) or _DEFAULT_AI_BASE_URL,
        model=values.get(AI_KEYS["model"], ""),
    )


def set_ai_config(db: Session, user_id: int, config: AIConfig) -> AIConfig:
    _set_value(db, user_id, AI_KEYS["api_key"], config.api_key)
    _set_value(db, user_id, AI_KEYS["base_url"], config.base_url)
    _set_value(db, user_id, AI_KEYS["model"], config.model)
    db.commit()
    return get_ai_config(db, user_id)


def get_tts_config(db: Session, user_id: int) -> TTSConfig:
    values = _get_values(db, user_id, list(TTS_KEYS.values()))
    return TTSConfig(api_key=values.get(TTS_KEYS["api_key"], ""))


def set_tts_config(db: Session, user_id: int, config: TTSConfig) -> TTSConfig:
    _set_value(db, user_id, TTS_KEYS["api_key"], config.api_key)
    db.commit()
    return get_tts_config(db, user_id)


def get_voices(db: Session, user_id: int) -> list[VoicePresetItem]:
    rows = (
        db.query(VoicePreset)
        .filter(VoicePreset.user_id == user_id)
        .order_by(VoicePreset.sort_order, VoicePreset.id)
        .all()
    )
    return [
        VoicePresetItem(
            voice_id=row.voice_id,
            name=row.name,
            lang=row.lang,
            resource_id=row.resource_id,
        )
        for row in rows
    ]


def set_voices(
    db: Session, user_id: int, voices: list[VoicePresetItem]
) -> list[VoicePresetItem]:
    """整表覆盖该用户的音色列表（忽略 voice_id 为空的行）。"""
    db.query(VoicePreset).filter(VoicePreset.user_id == user_id).delete()
    for order, item in enumerate(voices):
        voice_id = (item.voice_id or "").strip()
        if not voice_id:
            continue
        db.add(
            VoicePreset(
                user_id=user_id,
                voice_id=voice_id,
                name=(item.name or "").strip(),
                lang=(item.lang or "").strip(),
                resource_id=(item.resource_id or "").strip(),
                sort_order=order,
            )
        )
    db.commit()
    return get_voices(db, user_id)
