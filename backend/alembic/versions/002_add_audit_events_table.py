"""Add audit events table

Revision ID: 002_add_audit_events_table
Revises: 001_initial_policies_schema
Create Date: 2026-09-25 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_add_audit_events_table"
down_revision: Union[str, None] = "001_initial_policies_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=False),
        sa.Column("actor_username", sa.String(length=255), nullable=True),
        sa.Column("actor_roles", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("correlation_id", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_resource_type", "audit_events", ["resource_type"])
    op.create_index("ix_audit_events_resource_id", "audit_events", ["resource_id"])
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_correlation_id", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_id", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_type", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_table("audit_events")
