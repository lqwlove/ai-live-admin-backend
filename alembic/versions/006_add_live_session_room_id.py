"""add room_id to live_sessions

Revision ID: 006_live_session_room_id
Revises: 005_user_settings_voices
Create Date: 2026-06-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_live_session_room_id"
down_revision: Union[str, None] = "005_user_settings_voices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "live_sessions" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("live_sessions")}
    if "room_id" not in columns:
        op.add_column(
            "live_sessions",
            sa.Column("room_id", sa.String(length=128), nullable=False, server_default=""),
        )


def downgrade() -> None:
    op.drop_column("live_sessions", "room_id")
