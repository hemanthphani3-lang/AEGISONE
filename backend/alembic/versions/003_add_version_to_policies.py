"""Add version column to policies table

Revision ID: 003_add_version_to_policies
Revises: 002_add_audit_events_table
Create Date: 2026-09-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_add_version_to_policies"
down_revision: Union[str, None] = "002_add_audit_events_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "policies",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("policies", "version")
