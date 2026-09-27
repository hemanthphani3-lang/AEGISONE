"""Add incidents and incident_events tables

Revision ID: 006_incidents
Revises: 005_preserve_policy_versions
Create Date: 2026-09-27 14:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_incidents'
down_revision = '005_preserve_policy_versions_on_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='INTELLIGENCE_FINDING'),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('policy_id', sa.String(length=100), nullable=True),
        sa.Column('finding_id', sa.String(length=255), nullable=True),
        sa.Column('fingerprint', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_by', sa.String(length=255), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incidents_severity', 'incidents', ['severity'], unique=False)
    op.create_index('ix_incidents_status', 'incidents', ['status'], unique=False)
    op.create_index('ix_incidents_policy_id', 'incidents', ['policy_id'], unique=False)
    op.create_index('ix_incidents_fingerprint', 'incidents', ['fingerprint'], unique=False)
    op.create_index('ix_incidents_created_at', 'incidents', ['created_at'], unique=False)
    op.create_index('ix_incidents_assigned_to', 'incidents', ['assigned_to'], unique=False)
    op.create_index('ix_incidents_correlation_id', 'incidents', ['correlation_id'], unique=False)

    op.create_table(
        'incident_events',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('incident_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor_user_id', sa.String(length=255), nullable=False),
        sa.Column('actor_username', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incident_events_incident_id', 'incident_events', ['incident_id'], unique=False)
    op.create_index('ix_incident_events_event_type', 'incident_events', ['event_type'], unique=False)
    op.create_index('ix_incident_events_timestamp', 'incident_events', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('incident_events')
    op.drop_table('incidents')
