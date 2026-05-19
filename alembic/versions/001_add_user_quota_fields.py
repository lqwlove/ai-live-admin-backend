"""add user quota fields and billed_units on usage logs

Revision ID: 001_add_user_quota
Revises:
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_add_user_quota"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ai_token_limit", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("tts_chars_limit", sa.BigInteger(), nullable=True))
    op.add_column(
        "users",
        sa.Column("consumption_multiplier", sa.Numeric(4, 1), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "ai_token_usage_logs",
        sa.Column("billed_units", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tts_usage_logs",
        sa.Column("billed_units", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tts_usage_logs", "billed_units")
    op.drop_column("ai_token_usage_logs", "billed_units")
    op.drop_column("users", "consumption_multiplier")
    op.drop_column("users", "tts_chars_limit")
    op.drop_column("users", "ai_token_limit")
