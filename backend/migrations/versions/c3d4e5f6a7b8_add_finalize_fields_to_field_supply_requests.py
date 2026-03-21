"""add finalize fields to field supply requests

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("field_supply_requests", sa.Column("finalized_at", sa.DateTime(), nullable=True))
    op.add_column("field_supply_requests", sa.Column("finalized_by", sa.String(), nullable=True))
    op.add_column("field_supply_requests", sa.Column("finalize_method", sa.String(), nullable=True))
    op.add_column("field_supply_requests", sa.Column("finalize_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("field_supply_requests", "finalize_note")
    op.drop_column("field_supply_requests", "finalize_method")
    op.drop_column("field_supply_requests", "finalized_by")
    op.drop_column("field_supply_requests", "finalized_at")
