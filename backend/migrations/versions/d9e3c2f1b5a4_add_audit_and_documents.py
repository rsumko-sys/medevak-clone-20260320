"""add audit_log and case_documents

Revision ID: d9e3c2f1b5a4
Revises: c8f2b1a0d4e3
Create Date: 2025-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e3c2f1b5a4"
down_revision: Union[str, None] = "c8f2b1a0d4e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("row_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "case_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("case_documents")
    op.drop_table("audit_log")
