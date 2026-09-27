"""Add policy versions table

Revision ID: 004_add_policy_versions_table
Revises: 003_add_version_to_policies
Create Date: 2026-09-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_add_policy_versions_table"
down_revision: Union[str, None] = "003_add_version_to_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policy_versions",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("change_type", sa.String(length=50), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("changed_by_username", sa.String(length=255), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_id", "version", name="uq_policy_versions_policy_id_version"),
    )
    op.create_index("ix_policy_versions_policy_id", "policy_versions", ["policy_id"])
    op.create_index("ix_policy_versions_version", "policy_versions", ["version"])
    op.create_index("ix_policy_versions_changed_at", "policy_versions", ["changed_at"])


def downgrade() -> None:
    op.drop_index("ix_policy_versions_changed_at", table_name="policy_versions")
    op.drop_index("ix_policy_versions_version", table_name="policy_versions")
    op.drop_index("ix_policy_versions_policy_id", table_name="policy_versions")
    op.drop_table("policy_versions")
