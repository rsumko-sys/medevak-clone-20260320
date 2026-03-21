"""add dispatched_by and request_status to field_dispatch_logs

Revision ID: b1c2d3e4f5a6
Revises: 0dae98b2cb89
Create Date: 2026-03-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "0dae98b2cb89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("field_dispatch_logs", sa.Column("request_status", sa.String(), nullable=True))
    op.add_column("field_dispatch_logs", sa.Column("dispatched_by", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("field_dispatch_logs", "dispatched_by")
    op.drop_column("field_dispatch_logs", "request_status")
