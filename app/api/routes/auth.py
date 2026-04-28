from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(payload: LoginRequest, db: Session) -> User:
    stmt = select(User).where(or_(User.username == payload.username, User.email == payload.username))
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if user.status == "disabled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")
    return user


def _touch_login_and_build_token(user: User, db: Session) -> TokenResponse:
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), {"role": user.role})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = _authenticate_user(payload, db)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可登录后台")
    return _touch_login_and_build_token(user, db)


@router.post("/app-login", response_model=TokenResponse)
def app_login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = _authenticate_user(payload, db)
    return _touch_login_and_build_token(user, db)


@router.get("/me", response_model=UserOut)
def me(current_admin: User = Depends(get_current_admin)) -> User:
    return current_admin


@router.get("/app-me", response_model=UserOut)
def app_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
