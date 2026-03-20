"""hardening: role column, db indexes

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-03-18 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(), nullable=False, server_default="medic"))
    op.create_index("ix_cases_created_at", "cases", ["created_at"])
    op.create_index("ix_sync_queue_status", "sync_queue", ["status"])


def downgrade() -> None:
    op.drop_index("ix_sync_queue_status", "sync_queue")
    op.drop_index("ix_cases_created_at", "cases")
    op.drop_column("users", "role")
