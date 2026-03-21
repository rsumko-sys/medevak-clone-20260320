"""add composite lookup index for form_100_records

Revision ID: bb22cc33dd44
Revises: aa11bb22cc33
Create Date: 2026-03-21
"""

from alembic import op


revision = "bb22cc33dd44"
down_revision = "aa11bb22cc33"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_form_100_records_case_voided_created",
        "form_100_records",
        ["case_id", "voided", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_form_100_records_case_voided_created", table_name="form_100_records")
