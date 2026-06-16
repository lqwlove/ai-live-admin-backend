from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.quota_grant import QuotaGrant
from app.models.user import User
from app.schemas.common import ListResponse
from app.schemas.quota_grant import QuotaGrantCreate, QuotaGrantOut
from app.services.quota import lock_user_for_quota


router = APIRouter(
    prefix="/quota-grants",
    tags=["quota-grants"],
    dependencies=[Depends(get_current_admin)],
)


_LIMIT_FIELD = {
    "ai_token": "ai_token_limit",
    "tts_chars": "tts_chars_limit",
}


def _grant_out(grant: QuotaGrant) -> QuotaGrantOut:
    out = QuotaGrantOut.model_validate(grant)
    if grant.user is not None:
        out.user_username = grant.user.username
    return out


@router.get("", response_model=ListResponse[QuotaGrantOut])
def list_quota_grants(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    user_id: int | None = None,
    kind: str = "",
    sort: str = "id",
    order: str = "desc",
) -> dict:
    stmt = select(QuotaGrant)
    count_stmt = select(func.count()).select_from(QuotaGrant)
    conditions = []
    if user_id is not None:
        conditions.append(QuotaGrant.user_id == user_id)
    if kind:
        conditions.append(QuotaGrant.kind == kind)
    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    sort_column = getattr(QuotaGrant, sort, QuotaGrant.id)
    if order.lower() == "desc":
        sort_column = sort_column.desc()
    stmt = stmt.order_by(sort_column).offset((page - 1) * per_page).limit(per_page)

    grants = db.execute(stmt).scalars().all()
    total = db.execute(count_stmt).scalar_one()
    return {
        "data": [_grant_out(grant) for grant in grants],
        "total": total,
    }


@router.get("/{grant_id}", response_model=QuotaGrantOut)
def get_quota_grant(grant_id: int, db: Session = Depends(get_db)) -> QuotaGrantOut:
    grant = db.get(QuotaGrant, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="开通记录不存在")
    return _grant_out(grant)


@router.post("", response_model=QuotaGrantOut, status_code=status.HTTP_201_CREATED)
def create_quota_grant(
    payload: QuotaGrantCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> QuotaGrantOut:
    user = lock_user_for_quota(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    field = _LIMIT_FIELD[payload.kind]
    current = getattr(user, field) or 0
    new_limit = current + payload.amount
    setattr(user, field, new_limit)

    grant = QuotaGrant(
        user_id=user.id,
        kind=payload.kind,
        amount=payload.amount,
        limit_after=new_limit,
        note=payload.note,
        operator_id=admin.id,
        operator_username=admin.username,
    )
    db.add(user)
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return _grant_out(grant)
