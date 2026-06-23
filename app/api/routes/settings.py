from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, verify_integration_key
from app.db.session import get_db
from app.models.user import User
from app.schemas.settings import AIConfig, IntegrationConfig, TTSConfig
from app.services.settings import (
    get_ai_config,
    get_tts_config,
    set_ai_config,
    set_tts_config,
)


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_admin)],
)

integration_router = APIRouter(prefix="/integration/config", tags=["integration"])


@router.get("/ai", response_model=AIConfig)
def read_ai_config(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AIConfig:
    return get_ai_config(db)


@router.put("/ai", response_model=AIConfig)
def update_ai_config(
    payload: AIConfig,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AIConfig:
    return set_ai_config(db, payload)


@router.get("/tts", response_model=TTSConfig)
def read_tts_config(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> TTSConfig:
    return get_tts_config(db)


@router.put("/tts", response_model=TTSConfig)
def update_tts_config(
    payload: TTSConfig,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> TTSConfig:
    return set_tts_config(db, payload)


@integration_router.get("", response_model=IntegrationConfig)
def read_integration_config(
    db: Session = Depends(get_db),
    _: None = Depends(verify_integration_key),
) -> IntegrationConfig:
    return IntegrationConfig(ai=get_ai_config(db), tts=get_tts_config(db))
