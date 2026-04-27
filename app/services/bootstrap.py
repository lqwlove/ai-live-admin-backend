from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine
from app.models import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_initial_admin(db: Session) -> None:
    settings = get_settings()
    existing_admin = db.execute(select(User).where(User.role == "admin")).scalar_one_or_none()
    if existing_admin:
        return
    admin = User(
        username=settings.initial_admin_username,
        email=f"{settings.initial_admin_username}@local.admin",
        password_hash=get_password_hash(settings.initial_admin_password),
        role="admin",
        status="active",
    )
    db.add(admin)
    db.commit()
