"""add blood inventory tables

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-03-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blood_inventory",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("blood_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_blood_inventory_unit", "blood_inventory", ["unit"], unique=False)
    op.create_index(
        "ix_blood_inventory_unit_type",
        "blood_inventory",
        ["unit", "blood_type"],
        unique=True,
    )

    op.create_table(
        "blood_transactions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("blood_type", sa.String(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_blood_transactions_unit", "blood_transactions", ["unit"], unique=False)
    op.create_index("ix_blood_transactions_created_at", "blood_transactions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_blood_transactions_created_at", table_name="blood_transactions")
    op.drop_index("ix_blood_transactions_unit", table_name="blood_transactions")
    op.drop_table("blood_transactions")
    op.drop_index("ix_blood_inventory_unit_type", table_name="blood_inventory")
    op.drop_index("ix_blood_inventory_unit", table_name="blood_inventory")
    op.drop_table("blood_inventory")