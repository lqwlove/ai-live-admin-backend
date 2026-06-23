from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, verify_integration_key
from app.db.session import get_db
from app.models.user import User
from app.schemas.settings import (
    AIConfig,
    IntegrationConfig,
    TTSConfig,
    VoicePresetItem,
    VoicePresetList,
)
from app.services.settings import (
    get_ai_config,
    get_tts_config,
    get_voices,
    set_ai_config,
    set_tts_config,
    set_voices,
)


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
)

integration_router = APIRouter(prefix="/integration/config", tags=["integration"])


@router.get("/ai", response_model=AIConfig)
def read_ai_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIConfig:
    return get_ai_config(db, user.id)


@router.put("/ai", response_model=AIConfig)
def update_ai_config(
    payload: AIConfig,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIConfig:
    return set_ai_config(db, user.id, payload)


@router.get("/tts", response_model=TTSConfig)
def read_tts_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TTSConfig:
    return get_tts_config(db, user.id)


@router.put("/tts", response_model=TTSConfig)
def update_tts_config(
    payload: TTSConfig,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TTSConfig:
    return set_tts_config(db, user.id, payload)


@router.get("/voices", response_model=list[VoicePresetItem])
def read_voices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[VoicePresetItem]:
    return get_voices(db, user.id)


@router.put("/voices", response_model=list[VoicePresetItem])
def update_voices(
    payload: VoicePresetList,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[VoicePresetItem]:
    return set_voices(db, user.id, payload.voices)


@integration_router.get("", response_model=IntegrationConfig)
def read_integration_config(
    user_id: int = Query(..., description="拉取该用户的配置"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> IntegrationConfig:
    return IntegrationConfig(
        ai=get_ai_config(db, user_id),
        tts=get_tts_config(db, user_id),
        voices=get_voices(db, user_id),
    )
