"""add triage_code to case

Revision ID: c8f2b1a0d4e3
Revises: 73769e30d780
Create Date: 2025-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f2b1a0d4e3"
down_revision: Union[str, None] = "73769e30d780"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("triage_code", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "triage_code")
