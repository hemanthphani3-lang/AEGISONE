from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""

    pass


class DBPolicy(Base):
    """SQLAlchemy ORM model for policies table."""

    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    target_device_managed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    target_device_compliant: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relational collection children
    target_roles: Mapped[list["DBPolicyTargetRole"]] = relationship(
        "DBPolicyTargetRole",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    target_protocols: Mapped[list["DBPolicyTargetProtocol"]] = relationship(
        "DBPolicyTargetProtocol",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    target_locations: Mapped[list["DBPolicyTargetLocation"]] = relationship(
        "DBPolicyTargetLocation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    exclusions: Mapped[list["DBPolicyExclusion"]] = relationship(
        "DBPolicyExclusion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    excluded_users: Mapped[list["DBPolicyExcludedUser"]] = relationship(
        "DBPolicyExcludedUser",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DBPolicyTargetRole(Base):
    """Child table for policy target roles."""

    __tablename__ = "policy_target_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)


class DBPolicyTargetProtocol(Base):
    """Child table for policy target authentication protocols."""

    __tablename__ = "policy_target_protocols"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    protocol: Mapped[str] = mapped_column(String(50), nullable=False)


class DBPolicyTargetLocation(Base):
    """Child table for policy target locations."""

    __tablename__ = "policy_target_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    location: Mapped[str] = mapped_column(String(50), nullable=False)


class DBPolicyExclusion(Base):
    """Child table for policy excluded roles."""

    __tablename__ = "policy_exclusions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)


class DBPolicyExcludedUser(Base):
    """Child table for policy excluded user IDs."""

    __tablename__ = "policy_excluded_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)


class DBAuditEvent(Base):
    """SQLAlchemy ORM model for audit_events table."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    actor_user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    actor_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_roles: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(
        String(255), index=True, nullable=True
    )
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    correlation_id: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )


class DBPolicyVersion(Base):
    """SQLAlchemy ORM model for policy_versions immutable history table."""

    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("policies.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_by_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("policy_id", "version", name="uq_policy_versions_policy_id_version"),
    )


class DBIncident(Base):
    """SQLAlchemy ORM model for security incidents table."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="INTELLIGENCE_FINDING")
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    policy_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    finding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    events: Mapped[list["DBIncidentEvent"]] = relationship(
        "DBIncidentEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DBIncidentEvent.timestamp.asc()",
    )


class DBIncidentEvent(Base):
    """SQLAlchemy ORM model for immutable incident activity events."""

    __tablename__ = "incident_events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    incident: Mapped["DBIncident"] = relationship("DBIncident", back_populates="events")


