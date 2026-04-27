from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效登录状态")

    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.status == "disabled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")
    return user


def get_current_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def verify_integration_key(
    x_integration_api_key: Annotated[str | None, Header()] = None,
) -> None:
    expected = get_settings().integration_api_key
    if not x_integration_api_key or x_integration_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效接入密钥")
