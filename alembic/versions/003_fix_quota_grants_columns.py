"""make quota_grants schema converge to package model (idempotent)

Revision ID: 003_fix_quota_grants
Revises: 002_add_quota_grants
Create Date: 2026-06-16

针对历史上由 create_all 建出的旧结构 quota_grants（只有 amount/limit_after，
缺 consumed/multiplier）做幂等补列；对已是新结构的库则自动跳过。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_fix_quota_grants"
down_revision: Union[str, None] = "002_add_quota_grants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "quota_grants" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("quota_grants")}

    if "consumed" not in columns:
        op.add_column(
            "quota_grants",
            sa.Column("consumed", sa.BigInteger(), nullable=False, server_default="0"),
        )
    if "multiplier" not in columns:
        op.add_column(
            "quota_grants",
            sa.Column("multiplier", sa.Numeric(4, 1), nullable=False, server_default="1.0"),
        )
    if "limit_after" in columns:
        op.drop_column("quota_grants", "limit_after")


def downgrade() -> None:
    pass
