"""后台可配置项（AI / 语音合成）的读写服务。

以键值对存于 app_settings 表，key 形如 "ai.api_key"。
未配置时回退到下方默认值（与客户端历史内置值保持一致）。
"""

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.schemas.settings import AIConfig, TTSConfig

# 默认值（与 tk-live 客户端历史内置一致，作为未配置时的回退）
_DEFAULT_AI_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
_DEFAULT_TTS_SPEAKER_ID = "zh_female_vv_uranus_bigtts"
_DEFAULT_TTS_RESOURCE_ID = "seed-tts-2.0"

AI_KEYS = {
    "api_key": "ai.api_key",
    "base_url": "ai.base_url",
    "model": "ai.model",
}
TTS_KEYS = {
    "api_key": "tts.api_key",
    "speaker_id": "tts.speaker_id",
    "resource_id": "tts.resource_id",
}


def _get_values(db: Session, keys: list[str]) -> dict[str, str]:
    rows = db.query(AppSetting).filter(AppSetting.key.in_(keys)).all()
    return {row.key: row.value for row in rows}


def _set_value(db: Session, key: str, value: str) -> None:
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=value or ""))
    else:
        row.value = value or ""


def get_ai_config(db: Session) -> AIConfig:
    values = _get_values(db, list(AI_KEYS.values()))
    return AIConfig(
        api_key=values.get(AI_KEYS["api_key"], ""),
        base_url=values.get(AI_KEYS["base_url"]) or _DEFAULT_AI_BASE_URL,
        model=values.get(AI_KEYS["model"], ""),
    )


def set_ai_config(db: Session, config: AIConfig) -> AIConfig:
    _set_value(db, AI_KEYS["api_key"], config.api_key)
    _set_value(db, AI_KEYS["base_url"], config.base_url)
    _set_value(db, AI_KEYS["model"], config.model)
    db.commit()
    return get_ai_config(db)


def get_tts_config(db: Session) -> TTSConfig:
    values = _get_values(db, list(TTS_KEYS.values()))
    return TTSConfig(
        api_key=values.get(TTS_KEYS["api_key"], ""),
        speaker_id=values.get(TTS_KEYS["speaker_id"]) or _DEFAULT_TTS_SPEAKER_ID,
        resource_id=values.get(TTS_KEYS["resource_id"]) or _DEFAULT_TTS_RESOURCE_ID,
    )


def set_tts_config(db: Session, config: TTSConfig) -> TTSConfig:
    _set_value(db, TTS_KEYS["api_key"], config.api_key)
    _set_value(db, TTS_KEYS["speaker_id"], config.speaker_id)
    _set_value(db, TTS_KEYS["resource_id"], config.resource_id)
    db.commit()
    return get_tts_config(db)
