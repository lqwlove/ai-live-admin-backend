from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ListResponse
from app.schemas.user import PasswordReset, UserCreate, UserOut, UserUpdate


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_admin)])


def _ensure_unique_user(db: Session, username: str, email: str, exclude_id: int | None = None) -> None:
    stmt = select(User).where(or_(User.username == username, User.email == email))
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    exists = db.execute(stmt).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已存在")


@router.get("", response_model=ListResponse[UserOut])
def list_users(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    q: str = "",
    status_filter: str = Query(default="", alias="status"),
    sort: str = "id",
    order: str = "desc",
) -> dict:
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    conditions = []
    if q:
        like = f"%{q}%"
        conditions.append(or_(User.username.ilike(like), User.email.ilike(like)))
    if status_filter:
        conditions.append(User.status == status_filter)
    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    sort_column = getattr(User, sort, User.id)
    if order.lower() == "desc":
        sort_column = sort_column.desc()
    stmt = stmt.order_by(sort_column).offset((page - 1) * per_page).limit(per_page)

    users = db.execute(stmt).scalars().all()
    total = db.execute(count_stmt).scalar_one()
    return {"data": users, "total": total}


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    _ensure_unique_user(db, payload.username, payload.email)
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        status=payload.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    data = payload.model_dump(exclude_unset=True)
    next_username = data.get("username", user.username)
    next_email = data.get("email", user.email)
    if next_username != user.username or next_email != user.email:
        _ensure_unique_user(db, next_username, next_email, exclude_id=user.id)
    for key, value in data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", response_model=UserOut)
def reset_password(user_id: int, payload: PasswordReset, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.password_hash = get_password_hash(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
