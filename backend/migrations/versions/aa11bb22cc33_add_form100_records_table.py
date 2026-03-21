"""add form_100_records table

Revision ID: aa11bb22cc33
Revises: c3d4e5f6a7b8
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "aa11bb22cc33"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "form_100_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("document_number", sa.String(), nullable=False),
        sa.Column("injury_datetime", sa.DateTime(), nullable=False),
        sa.Column("injury_location", sa.String(), nullable=False),
        sa.Column("injury_mechanism", sa.String(), nullable=False),
        sa.Column("diagnosis_summary", sa.Text(), nullable=False),
        sa.Column("documented_by", sa.String(), nullable=False),
        sa.Column("treatment_summary", sa.Text(), nullable=True),
        sa.Column("evacuation_recommendation", sa.Text(), nullable=True),
        sa.Column("commander_notified", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("stub_json", sa.Text(), nullable=True),
        sa.Column("front_side_identity_json", sa.Text(), nullable=True),
        sa.Column("front_side_injury_json", sa.Text(), nullable=True),
        sa.Column("front_side_treatment_json", sa.Text(), nullable=True),
        sa.Column("front_side_evacuation_json", sa.Text(), nullable=True),
        sa.Column("front_side_triage_markers_json", sa.Text(), nullable=True),
        sa.Column("front_side_body_diagram_json", sa.Text(), nullable=True),
        sa.Column("back_side_stage_log_json", sa.Text(), nullable=True),
        sa.Column("back_side_signature_json", sa.Text(), nullable=True),
        sa.Column("meta_legal_rules_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("voided", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("form_100_records", schema=None) as batch_op:
        batch_op.create_index("ix_form_100_records_case_id", ["case_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("form_100_records", schema=None) as batch_op:
        batch_op.drop_index("ix_form_100_records_case_id")
    op.drop_table("form_100_records")
