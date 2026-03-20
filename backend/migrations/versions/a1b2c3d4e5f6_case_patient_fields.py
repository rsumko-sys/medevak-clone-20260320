"""case patient fields: add all CCRM patient columns to cases table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-03-18 01:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Patient identity
    op.add_column("cases", sa.Column("callsign", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("full_name", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("rank", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("unit", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("blood_type", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("dob", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("allergies", sa.String(), nullable=True))
    # Incident
    op.add_column("cases", sa.Column("incident_time", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("incident_location", sa.String(), nullable=True))
    # Evacuation
    op.add_column("cases", sa.Column("evac_status", sa.String(), nullable=True, server_default="очікує"))
    op.add_column("cases", sa.Column("evac_time", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("evac_dest", sa.String(), nullable=True))
    # MARCH
    op.add_column("cases", sa.Column("airway", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("breathing", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("circulation", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("disability", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("exposure", sa.String(), nullable=True))
    # JSON blobs
    op.add_column("cases", sa.Column("injuries_json", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("body_injuries_json", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("tourniquets_json", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("vitals_json", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("treatments_json", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("medications_json", sa.JSON(), nullable=True))
    # Metadata
    op.add_column("cases", sa.Column("created_by", sa.String(), nullable=True))


def downgrade() -> None:
    for col in [
        "created_by", "medications_json", "treatments_json", "vitals_json",
        "tourniquets_json", "body_injuries_json", "injuries_json",
        "exposure", "disability", "circulation", "breathing", "airway",
        "evac_dest", "evac_time", "evac_status",
        "incident_location", "incident_time",
        "allergies", "dob", "blood_type", "unit", "rank", "full_name", "callsign",
    ]:
        op.drop_column("cases", col)
