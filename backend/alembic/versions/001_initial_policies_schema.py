"""Initial policies schema

Revision ID: 001_initial_policies_schema
Revises: 
Create Date: 2026-09-24 22:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_policies_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target_device_managed", sa.Boolean(), nullable=True),
        sa.Column("target_device_compliant", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_target_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_target_protocols",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("protocol", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_target_locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_exclusions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "policy_excluded_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("policy_excluded_users")
    op.drop_table("policy_exclusions")
    op.drop_table("policy_target_locations")
    op.drop_table("policy_target_protocols")
    op.drop_table("policy_target_roles")
    op.drop_table("policies")
