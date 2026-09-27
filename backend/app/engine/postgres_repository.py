from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.converters import from_domain_policy, to_domain_policy
from app.db.models import (
    DBPolicy,
    DBPolicyExcludedUser,
    DBPolicyExclusion,
    DBPolicyTargetLocation,
    DBPolicyTargetProtocol,
    DBPolicyTargetRole,
    DBPolicyVersion,
)
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import Policy
from app.engine.repository import AbstractPolicyRepository


class PostgresPolicyRepository(AbstractPolicyRepository):
    """PostgreSQL concrete policy repository using SQLAlchemy 2.x async sessions.

    Converts ORM models to domain Policy models to keep PolicyEvaluator database-agnostic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_select(self):
        return select(DBPolicy).options(
            selectinload(DBPolicy.target_roles),
            selectinload(DBPolicy.target_protocols),
            selectinload(DBPolicy.target_locations),
            selectinload(DBPolicy.exclusions),
            selectinload(DBPolicy.excluded_users),
        )

    async def get_all_async(self) -> list[Policy]:
        """Retrieve all active policies asynchronously."""
        stmt = self._base_select()
        result = await self.session.execute(stmt)
        db_policies = result.scalars().all()
        if not db_policies:
            from app.engine.repository import DEFAULT_POLICIES
            for p in DEFAULT_POLICIES:
                db_p = from_domain_policy(p)
                self.session.add(db_p)
            await self.session.commit()
            stmt = self._base_select()
            result = await self.session.execute(stmt)
            db_policies = result.scalars().all()
        return [to_domain_policy(p) for p in db_policies]

    async def get_by_id_async(self, policy_id: str, for_update: bool = False) -> Policy | None:
        """Retrieve a single policy by ID asynchronously with optional FOR UPDATE row locking."""
        stmt = self._base_select().where(DBPolicy.id == policy_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        db_policy = result.scalar_one_or_none()
        if not db_policy:
            return None
        return to_domain_policy(db_policy)

    async def create_async(self, policy: Policy) -> Policy:
        """Create a new policy in PostgreSQL."""
        existing = await self.session.get(DBPolicy, policy.id)
        if existing:
            raise ValueError(f"Policy with ID '{policy.id}' already exists.")

        db_policy = from_domain_policy(policy)
        self.session.add(db_policy)
        await self.session.commit()
        created = await self.get_by_id_async(policy.id)
        return created or policy

    async def update_async(self, policy_id: str, update_data: dict) -> Policy | None:
        """Update mutable policy fields in PostgreSQL with FOR UPDATE row locking."""
        stmt = self._base_select().where(DBPolicy.id == policy_id).with_for_update()
        result = await self.session.execute(stmt)
        db_policy = result.scalar_one_or_none()
        if not db_policy:
            return None

        # Increment version on update
        db_policy.version = (db_policy.version or 1) + 1

        # Update scalar fields
        if "name" in update_data and update_data["name"] is not None:
            db_policy.name = update_data["name"]
        if "description" in update_data and update_data["description"] is not None:
            db_policy.description = update_data["description"]
        if "enabled" in update_data and update_data["enabled"] is not None:
            db_policy.enabled = update_data["enabled"]
        if "action" in update_data and update_data["action"] is not None:
            action_val = update_data["action"]
            db_policy.action = (
                action_val.value if isinstance(action_val, PolicyDecision) else str(action_val)
            )
        if "target_device_managed" in update_data:
            db_policy.target_device_managed = update_data["target_device_managed"]
        if "target_device_compliant" in update_data:
            db_policy.target_device_compliant = update_data["target_device_compliant"]

        # Update relationship collections if provided
        if "target_roles" in update_data and update_data["target_roles"] is not None:
            db_policy.target_roles.clear()
            for r in update_data["target_roles"]:
                val = r.value if isinstance(r, UserRole) else str(r)
                db_policy.target_roles.append(DBPolicyTargetRole(role=val))

        if "target_protocols" in update_data and update_data["target_protocols"] is not None:
            db_policy.target_protocols.clear()
            for p in update_data["target_protocols"]:
                val = p.value if isinstance(p, AuthProtocol) else str(p)
                db_policy.target_protocols.append(DBPolicyTargetProtocol(protocol=val))

        if "target_locations" in update_data and update_data["target_locations"] is not None:
            db_policy.target_locations.clear()
            for loc in update_data["target_locations"]:
                db_policy.target_locations.append(DBPolicyTargetLocation(location=loc))

        if "exclusions" in update_data and update_data["exclusions"] is not None:
            db_policy.exclusions.clear()
            for ex in update_data["exclusions"]:
                val = ex.value if isinstance(ex, UserRole) else str(ex)
                db_policy.exclusions.append(DBPolicyExclusion(role=val))

        if "excluded_users" in update_data and update_data["excluded_users"] is not None:
            db_policy.excluded_users.clear()
            for uid in update_data["excluded_users"]:
                db_policy.excluded_users.append(DBPolicyExcludedUser(user_id=uid))

        await self.session.commit()
        return await self.get_by_id_async(policy_id)

    async def delete_async(self, policy_id: str) -> bool:
        """Delete a policy by ID."""
        stmt = select(DBPolicy).where(DBPolicy.id == policy_id)
        result = await self.session.execute(stmt)
        db_policy = result.scalar_one_or_none()
        if not db_policy:
            return False

        await self.session.delete(db_policy)
        await self.session.commit()
        return True

    async def record_version_async(self, db_version: DBPolicyVersion) -> None:
        """Record an immutable policy version snapshot."""
        self.session.add(db_version)

    async def get_versions_async(self, policy_id: str) -> list[DBPolicyVersion]:
        """Retrieve all historical version snapshots for a policy sorted descending by version."""
        stmt = (
            select(DBPolicyVersion)
            .where(DBPolicyVersion.policy_id == policy_id)
            .order_by(DBPolicyVersion.version.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_version_by_number_async(self, policy_id: str, version: int) -> DBPolicyVersion | None:
        """Retrieve a specific historical version snapshot."""
        stmt = select(DBPolicyVersion).where(
            DBPolicyVersion.policy_id == policy_id,
            DBPolicyVersion.version == version,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # Implement AbstractPolicyRepository interface sync fallback (if called sync)
    def get_all(self) -> list[Policy]:
        """Synchronous wrapper for get_all."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            # If in event loop, raise RuntimeError or use async
            return loop.run_until_complete(self.get_all_async())
        except RuntimeError:
            return asyncio.run(self.get_all_async())

    def get_by_id(self, policy_id: str) -> Policy | None:
        """Synchronous wrapper for get_by_id."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.get_by_id_async(policy_id))
        except RuntimeError:
            return asyncio.run(self.get_by_id_async(policy_id))
