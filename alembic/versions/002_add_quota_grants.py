"""add quota_grants table (independent quota packages)

Revision ID: 002_add_quota_grants
Revises: 001_add_user_quota
Create Date: 2026-06-16

每个额度包是一条独立记录，含独立余额(consumed)与倍率(multiplier)，
消耗时按开通顺序 FIFO 先用先扣。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_add_quota_grants"
down_revision: Union[str, None] = "001_add_user_quota"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quota_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("consumed", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("multiplier", sa.Numeric(4, 1), nullable=False, server_default="1.0"),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("operator_username", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quota_grants_id", "quota_grants", ["id"])
    op.create_index("ix_quota_grants_user_id", "quota_grants", ["user_id"])
    op.create_index("ix_quota_grants_kind", "quota_grants", ["kind"])
    op.create_index("ix_quota_grants_operator_id", "quota_grants", ["operator_id"])


def downgrade() -> None:
    op.drop_index("ix_quota_grants_operator_id", table_name="quota_grants")
    op.drop_index("ix_quota_grants_kind", table_name="quota_grants")
    op.drop_index("ix_quota_grants_user_id", table_name="quota_grants")
    op.drop_index("ix_quota_grants_id", table_name="quota_grants")
    op.drop_table("quota_grants")
