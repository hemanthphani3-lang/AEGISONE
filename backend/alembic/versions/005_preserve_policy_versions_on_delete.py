"""Preserve policy versions on delete migration

Revision ID: 005_preserve_policy_versions_on_delete
Revises: 004_add_policy_versions_table
Create Date: 2026-09-27 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_preserve_policy_versions_on_delete"
down_revision: Union[str, None] = "004_add_policy_versions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop foreign key constraint with ondelete CASCADE and recreate without CASCADE
    try:
        op.drop_constraint("policy_versions_policy_id_fkey", "policy_versions", type_="foreignkey")
    except Exception:
        pass
    op.create_foreign_key(
        "policy_versions_policy_id_fkey",
        "policy_versions",
        "policies",
        ["policy_id"],
        ["id"],
    )


def downgrade() -> None:
    try:
        op.drop_constraint("policy_versions_policy_id_fkey", "policy_versions", type_="foreignkey")
    except Exception:
        pass
    op.create_foreign_key(
        "policy_versions_policy_id_fkey",
        "policy_versions",
        "policies",
        ["policy_id"],
        ["id"],
        ondelete="CASCADE",
    )
