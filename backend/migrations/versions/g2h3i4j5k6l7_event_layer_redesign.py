"""Event layer redesign — generic domain event store.

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("events")

    op.create_table(
        "events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_events_entity_id", "events", ["entity_id"])
    op.create_index("ix_events_unit", "events", ["unit"])
    op.create_index("ix_events_unit_created_at", "events", ["unit", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_events_unit_created_at")
    op.drop_index("ix_events_unit")
    op.drop_index("ix_events_entity_id")
    op.drop_table("events")

    op.create_table(
        "events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_time", sa.DateTime()),
        sa.Column("actor_id", sa.String()),
        sa.Column("payload", sa.JSON()),
        sa.Column("recorded_at", sa.DateTime()),
        sa.Column("voided", sa.Boolean(), default=False),
    )
    op.create_index("ix_events_case_id", "events", ["case_id"])
