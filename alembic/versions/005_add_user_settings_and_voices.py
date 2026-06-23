"""add user_settings and voice_presets tables

Revision ID: 005_user_settings_voices
Revises: 004_add_app_settings
Create Date: 2026-06-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_user_settings_voices"
down_revision: Union[str, None] = "004_add_app_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "user_settings" not in existing:
        op.create_table(
            "user_settings",
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("key", sa.String(length=128), nullable=False),
            sa.Column("value", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "key"),
        )

    if "voice_presets" not in existing:
        op.create_table(
            "voice_presets",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("voice_id", sa.String(length=128), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("lang", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("resource_id", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_voice_presets_user_id", "voice_presets", ["user_id"], unique=False
        )


def downgrade() -> None:
    op.drop_index("ix_voice_presets_user_id", table_name="voice_presets")
    op.drop_table("voice_presets")
    op.drop_table("user_settings")
