from datetime import datetime, timezone
import json
from typing import Any
import uuid
from fastapi import HTTPException, status
from app.audit.enums import AuditEventType, AuditOutcome
from app.audit.service import audit_service
from app.auth.models import AuthenticatedUser
from app.core.correlation import get_correlation_id
from app.db.models import DBPolicyVersion
from app.db.session import async_session_factory, check_database_connection
from app.engine.diff_engine import compute_policy_diff
from app.engine.models import (
    Policy,
    PolicyCreate,
    PolicyDiffResponse,
    PolicyRollbackRequest,
    PolicyUpdate,
    PolicyValidationResponse,
    PolicyVersionDetail,
    PolicyVersionListResponse,
    PolicyVersionSummary,
)
from app.engine.postgres_repository import PostgresPolicyRepository
from app.engine.repository import policy_repository as in_memory_repo
from app.engine.validator import validate_policy_definition


class PolicyService:
    """Service layer for policy management, validation, history snapshots, and repository coordination."""

    @staticmethod
    def _validate_policy_id(policy_id: str) -> str:
        """Validate that policy ID is non-empty and non-whitespace."""
        if not policy_id or not policy_id.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Policy ID cannot be empty or whitespace.",
            )
        return policy_id.strip()

    @staticmethod
    def _validate_policy_payload(name: str | None, description: str | None) -> None:
        """Validate policy name and description attributes."""
        if name is not None and (not name or not name.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Policy name cannot be empty or whitespace.",
            )
        if description is not None and (not description or not description.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Policy description cannot be empty or whitespace.",
            )

    @staticmethod
    def validate_policy_payload(data: dict | PolicyCreate | PolicyUpdate | Any, is_create: bool = False) -> PolicyValidationResponse:
        """Centralized validation endpoint function."""
        return validate_policy_definition(data, is_create=is_create)

    @staticmethod
    async def get_active_repository():
        """Retrieve active repository (Postgres if connected, else In-Memory)."""
        if await check_database_connection():
            session = async_session_factory()
            return PostgresPolicyRepository(session), session
        return in_memory_repo, None

    async def _record_version_snapshot(
        self,
        policy: Policy,
        change_type: str,
        actor: AuthenticatedUser | None,
        session: Any | None = None,
    ) -> DBPolicyVersion | dict:
        """Helper to create an immutable policy version snapshot."""
        actor_id = actor.user_id if actor else "SYSTEM"
        actor_name = actor.username if actor else "system"
        corr_id = get_correlation_id()
        ver_id = f"pver_{uuid.uuid4().hex[:16]}"
        snapshot_str = policy.model_dump_json()

        db_version = DBPolicyVersion(
            id=ver_id,
            policy_id=policy.id,
            version=policy.version,
            snapshot_json=snapshot_str,
            change_type=change_type,
            changed_by_user_id=actor_id,
            changed_by_username=actor_name,
            changed_at=datetime.now(timezone.utc),
            correlation_id=corr_id,
        )

        if session:
            session.add(db_version)
            await audit_service.record_event(
                event_type=AuditEventType.POLICY_VERSION_CREATED,
                action="CREATE_POLICY_VERSION",
                resource_type="POLICY_VERSION",
                resource_id=db_version.id,
                outcome=AuditOutcome.SUCCESS,
                metadata={"policy_id": policy.id, "version": policy.version, "change_type": change_type},
                actor=actor,
                session=session,
            )
        else:
            if not hasattr(in_memory_repo, "_history"):
                in_memory_repo._history = {}
            if policy.id not in in_memory_repo._history:
                in_memory_repo._history[policy.id] = []
            history_entry = {
                "id": ver_id,
                "policy_id": policy.id,
                "version": policy.version,
                "snapshot_json": snapshot_str,
                "change_type": change_type,
                "changed_by_user_id": actor_id,
                "changed_by_username": actor_name,
                "changed_at": datetime.now(timezone.utc),
                "correlation_id": corr_id,
            }
            in_memory_repo._history[policy.id].append(history_entry)
            await audit_service.record_event(
                event_type=AuditEventType.POLICY_VERSION_CREATED,
                action="CREATE_POLICY_VERSION",
                resource_type="POLICY_VERSION",
                resource_id=ver_id,
                outcome=AuditOutcome.SUCCESS,
                metadata={"policy_id": policy.id, "version": policy.version, "change_type": change_type},
                actor=actor,
            )
        return db_version

    async def list_policies(self) -> list[Policy]:
        """Retrieve all available policies."""
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                return await repo.get_all_async()
            return repo.get_all()
        finally:
            if session:
                await session.close()

    async def get_policy_by_id(self, policy_id: str) -> Policy:
        """Retrieve a single policy by ID."""
        cleaned_id = self._validate_policy_id(policy_id)
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                policy = await repo.get_by_id_async(cleaned_id)
            else:
                policy = repo.get_by_id(cleaned_id)

            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Policy '{cleaned_id}' not found",
                )
            return policy
        finally:
            if session:
                await session.close()

    async def create_policy(
        self, payload: PolicyCreate, actor: AuthenticatedUser | None = None
    ) -> Policy:
        """Create a new policy with validation, conflict checking, snapshot creation, and audit logging."""
        cleaned_id = self._validate_policy_id(payload.id)
        self._validate_policy_payload(payload.name, payload.description)
        
        # Centralized validation check
        val_res = validate_policy_definition(payload, is_create=True)
        if not val_res.valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "POLICY_VALIDATION_ERROR",
                    "message": val_res.errors[0] if val_res.errors else "Policy validation failed.",
                    "errors": val_res.errors,
                    "warnings": val_res.warnings,
                },
            )

        domain_policy = Policy(**payload.model_dump(exclude={"id"}), id=cleaned_id)
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                existing = await repo.get_by_id_async(cleaned_id)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Policy with ID '{cleaned_id}' already exists.",
                    )
                res = await repo.create_async(domain_policy)
                await self._record_version_snapshot(res, "CREATE", actor, session=session)
                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_CREATED,
                    action="CREATE_POLICY",
                    resource_type="POLICY",
                    resource_id=res.id,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={"name": res.name, "action": res.action.value, "version": res.version},
                    actor=actor,
                    session=session,
                )
                await session.commit()
                return res
            else:
                if repo.get_by_id(cleaned_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Policy with ID '{cleaned_id}' already exists.",
                    )
                repo._policies[cleaned_id] = domain_policy
                await self._record_version_snapshot(domain_policy, "CREATE", actor, session=None)
                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_CREATED,
                    action="CREATE_POLICY",
                    resource_type="POLICY",
                    resource_id=domain_policy.id,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={"name": domain_policy.name, "action": domain_policy.action.value, "version": domain_policy.version},
                    actor=actor,
                )
                return domain_policy
        finally:
            if session:
                await session.close()

    async def update_policy(
        self,
        policy_id: str,
        payload: PolicyUpdate,
        actor: AuthenticatedUser | None = None,
    ) -> Policy:
        """Safely perform partial update on an existing policy with OCC, snapshot creation, and audit logging."""
        cleaned_id = self._validate_policy_id(policy_id)
        self._validate_policy_payload(payload.name, payload.description)
        
        # Centralized validation check
        val_res = validate_policy_definition(payload, is_create=False)
        if not val_res.valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "POLICY_VALIDATION_ERROR",
                    "message": val_res.errors[0] if val_res.errors else "Policy validation failed.",
                    "errors": val_res.errors,
                    "warnings": val_res.warnings,
                },
            )

        update_data = payload.model_dump(exclude_unset=True)
        expected_ver = payload.expected_version if payload.expected_version is not None else payload.version

        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                existing = await repo.get_by_id_async(cleaned_id, for_update=True)
                if not existing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Policy '{cleaned_id}' not found",
                    )
                
                # Optimistic Concurrency Control Check
                if expected_ver is not None and existing.version != expected_ver:
                    await audit_service.record_event(
                        event_type=AuditEventType.POLICY_CONFLICT,
                        action="UPDATE_POLICY_CONFLICT",
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.FAILURE,
                        metadata={
                            "expected_version": expected_ver,
                            "current_version": existing.version,
                            "reason": f"Optimistic concurrency conflict for policy '{cleaned_id}'. Expected version {expected_ver}, current version is {existing.version}.",
                        },
                        actor=actor,
                        session=session,
                    )
                    await session.commit()
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": "POLICY_CONCURRENCY_CONFLICT",
                            "message": f"Policy '{cleaned_id}' has been modified by another administrator (expected version {expected_ver}, current version {existing.version}). Please refresh before saving.",
                            "policy_id": cleaned_id,
                            "expected_version": expected_ver,
                            "current_version": existing.version,
                        },
                    )

                prev_enabled = existing.enabled
                updated = await repo.update_async(cleaned_id, update_data)
                changed_fields = sorted(list(update_data.keys()))

                change_type = "UPDATE"
                if "enabled" in update_data and prev_enabled != updated.enabled:
                    change_type = "ENABLE" if updated.enabled else "DISABLE"

                await self._record_version_snapshot(updated, change_type, actor, session=session)

                if "enabled" in update_data and prev_enabled != updated.enabled:
                    evt_type = (
                        AuditEventType.POLICY_ENABLED
                        if updated.enabled
                        else AuditEventType.POLICY_DISABLED
                    )
                    act = "ENABLE_POLICY" if updated.enabled else "DISABLE_POLICY"
                    await audit_service.record_event(
                        event_type=evt_type,
                        action=act,
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.SUCCESS,
                        metadata={
                            "previous_state": prev_enabled,
                            "new_state": updated.enabled,
                            "changed_fields": changed_fields,
                            "version": updated.version,
                        },
                        actor=actor,
                        session=session,
                    )
                else:
                    await audit_service.record_event(
                        event_type=AuditEventType.POLICY_UPDATED,
                        action="UPDATE_POLICY",
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.SUCCESS,
                        metadata={"changed_fields": changed_fields, "version": updated.version},
                        actor=actor,
                        session=session,
                    )
                await session.commit()
                return updated
            else:
                existing = repo.get_by_id(cleaned_id)
                if not existing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Policy '{cleaned_id}' not found",
                    )
                
                # Optimistic Concurrency Control Check for in-memory repo
                if expected_ver is not None and existing.version != expected_ver:
                    await audit_service.record_event(
                        event_type=AuditEventType.POLICY_CONFLICT,
                        action="UPDATE_POLICY_CONFLICT",
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.FAILURE,
                        metadata={
                            "expected_version": expected_ver,
                            "current_version": existing.version,
                            "reason": f"Optimistic concurrency conflict for policy '{cleaned_id}'. Expected version {expected_ver}, current version is {existing.version}.",
                        },
                        actor=actor,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": "POLICY_CONCURRENCY_CONFLICT",
                            "message": f"Policy '{cleaned_id}' has been modified by another administrator (expected version {expected_ver}, current version {existing.version}). Please refresh before saving.",
                            "policy_id": cleaned_id,
                            "expected_version": expected_ver,
                            "current_version": existing.version,
                        },
                    )

                prev_enabled = existing.enabled
                updated_fields = existing.model_dump()
                updated_fields.update(update_data)
                updated_fields["version"] = (existing.version or 1) + 1
                updated_policy = Policy(**updated_fields)
                repo._policies[cleaned_id] = updated_policy
                changed_fields = sorted(list(update_data.keys()))

                change_type = "UPDATE"
                if "enabled" in update_data and prev_enabled != updated_policy.enabled:
                    change_type = "ENABLE" if updated_policy.enabled else "DISABLE"

                await self._record_version_snapshot(updated_policy, change_type, actor, session=None)

                if "enabled" in update_data and prev_enabled != updated_policy.enabled:
                    evt_type = (
                        AuditEventType.POLICY_ENABLED
                        if updated_policy.enabled
                        else AuditEventType.POLICY_DISABLED
                    )
                    act = "ENABLE_POLICY" if updated_policy.enabled else "DISABLE_POLICY"
                    await audit_service.record_event(
                        event_type=evt_type,
                        action=act,
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.SUCCESS,
                        metadata={
                            "previous_state": prev_enabled,
                            "new_state": updated_policy.enabled,
                            "changed_fields": changed_fields,
                            "version": updated_policy.version,
                        },
                        actor=actor,
                    )
                else:
                    await audit_service.record_event(
                        event_type=AuditEventType.POLICY_UPDATED,
                        action="UPDATE_POLICY",
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.SUCCESS,
                        metadata={"changed_fields": changed_fields, "version": updated_policy.version},
                        actor=actor,
                    )
                return updated_policy
        finally:
            if session:
                await session.close()

    async def delete_policy(
        self, policy_id: str, actor: AuthenticatedUser | None = None
    ) -> dict[str, str]:
        """Delete a policy by ID with audit logging."""
        cleaned_id = self._validate_policy_id(policy_id)
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                deleted = await repo.delete_async(cleaned_id)
                if not deleted:
                    await audit_service.record_event(
                        event_type=AuditEventType.POLICY_DELETED,
                        action="DELETE_POLICY",
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.FAILURE,
                        metadata={"reason": "Policy not found"},
                        actor=actor,
                        session=session,
                    )
                    await session.commit()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Policy '{cleaned_id}' not found",
                    )
                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_DELETED,
                    action="DELETE_POLICY",
                    resource_type="POLICY",
                    resource_id=cleaned_id,
                    outcome=AuditOutcome.SUCCESS,
                    actor=actor,
                    session=session,
                )
                await session.commit()
                return {"status": "deleted", "id": cleaned_id}
            else:
                existing = repo.get_by_id(cleaned_id)
                if not existing:
                    await audit_service.record_event(
                        event_type=AuditEventType.POLICY_DELETED,
                        action="DELETE_POLICY",
                        resource_type="POLICY",
                        resource_id=cleaned_id,
                        outcome=AuditOutcome.FAILURE,
                        metadata={"reason": "Policy not found"},
                        actor=actor,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Policy '{cleaned_id}' not found",
                    )
                del repo._policies[cleaned_id]
                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_DELETED,
                    action="DELETE_POLICY",
                    resource_type="POLICY",
                    resource_id=cleaned_id,
                    outcome=AuditOutcome.SUCCESS,
                    actor=actor,
                )
                return {"status": "deleted", "id": cleaned_id}
        finally:
            if session:
                await session.close()

    async def get_policy_versions(self, policy_id: str) -> PolicyVersionListResponse:
        """Retrieve all historical version snapshot summaries for a policy."""
        cleaned_id = self._validate_policy_id(policy_id)
        await self.get_policy_by_id(cleaned_id)
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                versions = await repo.get_versions_async(cleaned_id)
                summaries = [
                    PolicyVersionSummary(
                        id=v.id,
                        policy_id=v.policy_id,
                        version=v.version,
                        change_type=v.change_type,
                        changed_by_user_id=v.changed_by_user_id,
                        changed_by_username=v.changed_by_username,
                        changed_at=v.changed_at,
                        correlation_id=v.correlation_id,
                    )
                    for v in versions
                ]
                return PolicyVersionListResponse(versions=summaries)
            else:
                raw_history = getattr(in_memory_repo, "_history", {}).get(cleaned_id, [])
                sorted_history = sorted(raw_history, key=lambda item: item["version"], reverse=True)
                summaries = [
                    PolicyVersionSummary(
                        id=h["id"],
                        policy_id=h["policy_id"],
                        version=h["version"],
                        change_type=h["change_type"],
                        changed_by_user_id=h["changed_by_user_id"],
                        changed_by_username=h.get("changed_by_username"),
                        changed_at=h["changed_at"],
                        correlation_id=h["correlation_id"],
                    )
                    for h in sorted_history
                ]
                return PolicyVersionListResponse(versions=summaries)
        finally:
            if session:
                await session.close()

    async def get_policy_version_detail(self, policy_id: str, version: int) -> PolicyVersionDetail:
        """Retrieve detailed snapshot for a specific policy version."""
        cleaned_id = self._validate_policy_id(policy_id)
        await self.get_policy_by_id(cleaned_id)
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                db_ver = await repo.get_version_by_number_async(cleaned_id, version)
                if not db_ver:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Version {version} for policy '{cleaned_id}' not found",
                    )
                snapshot_data = json.loads(db_ver.snapshot_json)
                snapshot_policy = Policy(**snapshot_data)
                return PolicyVersionDetail(
                    id=db_ver.id,
                    policy_id=db_ver.policy_id,
                    version=db_ver.version,
                    snapshot=snapshot_policy,
                    change_type=db_ver.change_type,
                    changed_by_user_id=db_ver.changed_by_user_id,
                    changed_by_username=db_ver.changed_by_username,
                    changed_at=db_ver.changed_at,
                    correlation_id=db_ver.correlation_id,
                )
            else:
                raw_history = getattr(in_memory_repo, "_history", {}).get(cleaned_id, [])
                match = next((h for h in raw_history if h["version"] == version), None)
                if not match:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Version {version} for policy '{cleaned_id}' not found",
                    )
                snapshot_data = json.loads(match["snapshot_json"])
                snapshot_policy = Policy(**snapshot_data)
                return PolicyVersionDetail(
                    id=match["id"],
                    policy_id=match["policy_id"],
                    version=match["version"],
                    snapshot=snapshot_policy,
                    change_type=match["change_type"],
                    changed_by_user_id=match["changed_by_user_id"],
                    changed_by_username=match.get("changed_by_username"),
                    changed_at=match["changed_at"],
                    correlation_id=match["correlation_id"],
                )
        finally:
            if session:
                await session.close()

    async def get_policy_version_diff(
        self, policy_id: str, version: int, against_version: int | None = None
    ) -> PolicyDiffResponse:
        """Compare two policy versions and return field-level diffs."""
        cleaned_id = self._validate_policy_id(policy_id)
        target_ver_detail = await self.get_policy_version_detail(cleaned_id, version)
        
        if against_version is not None:
            base_ver_detail = await self.get_policy_version_detail(cleaned_id, against_version)
            return compute_policy_diff(target_ver_detail.snapshot, base_ver_detail.snapshot)
        else:
            current_policy = await self.get_policy_by_id(cleaned_id)
            return compute_policy_diff(target_ver_detail.snapshot, current_policy)

    async def rollback_policy(
        self,
        policy_id: str,
        payload: PolicyRollbackRequest,
        actor: AuthenticatedUser | None = None,
    ) -> Policy:
        """Rollback policy to a historical version snapshot as a new current version."""
        cleaned_id = self._validate_policy_id(policy_id)
        current_policy = await self.get_policy_by_id(cleaned_id)

        # 1. Optimistic Concurrency Control Check on Rollback
        if (
            payload.expected_current_version is not None
            and current_policy.version != payload.expected_current_version
        ):
            repo, session = await self.get_active_repository()
            try:
                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_CONFLICT,
                    action="ROLLBACK_POLICY_CONFLICT",
                    resource_type="POLICY",
                    resource_id=cleaned_id,
                    outcome=AuditOutcome.FAILURE,
                    metadata={
                        "expected_version": payload.expected_current_version,
                        "current_version": current_policy.version,
                        "reason": f"Rollback conflict for policy '{cleaned_id}'. Current version is {current_policy.version} but expected {payload.expected_current_version}.",
                    },
                    actor=actor,
                    session=session,
                )
                if session:
                    await session.commit()
            finally:
                if session:
                    await session.close()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "POLICY_CONCURRENCY_CONFLICT",
                    "message": f"Policy '{cleaned_id}' has been modified by another administrator (expected version {payload.expected_current_version}, current version {current_policy.version}). Please refresh before attempting rollback.",
                    "policy_id": cleaned_id,
                    "expected_version": payload.expected_current_version,
                    "current_version": current_policy.version,
                },
            )

        # 2. Retrieve historical snapshot
        target_ver_detail = await self.get_policy_version_detail(cleaned_id, payload.target_version)
        snapshot_policy = target_ver_detail.snapshot

        # 3. Validate reconstructed policy snapshot
        val_res = validate_policy_definition(snapshot_policy, is_create=False)
        if not val_res.valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "POLICY_VALIDATION_ERROR",
                    "message": val_res.errors[0] if val_res.errors else "Historical policy validation failed.",
                    "errors": val_res.errors,
                    "warnings": val_res.warnings,
                },
            )

        # 4. Construct update payload restoring attributes from snapshot
        update_payload = PolicyUpdate(
            name=snapshot_policy.name,
            description=snapshot_policy.description,
            enabled=snapshot_policy.enabled,
            target_roles=snapshot_policy.target_roles,
            target_protocols=snapshot_policy.target_protocols,
            target_locations=snapshot_policy.target_locations,
            target_device_managed=snapshot_policy.target_device_managed,
            target_device_compliant=snapshot_policy.target_device_compliant,
            target_risk_level=snapshot_policy.target_risk_level,
            action=snapshot_policy.action,
            exclusions=snapshot_policy.exclusions,
            excluded_users=snapshot_policy.excluded_users,
        )

        update_data = update_payload.model_dump(exclude_unset=True)
        repo, session = await self.get_active_repository()
        try:
            if isinstance(repo, PostgresPolicyRepository):
                existing = await repo.get_by_id_async(cleaned_id)
                prev_version = existing.version
                updated_policy = await repo.update_async(cleaned_id, update_data)
                
                # Record snapshot with ROLLBACK change_type
                await self._record_version_snapshot(updated_policy, "ROLLBACK", actor, session=session)

                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_ROLLED_BACK,
                    action="ROLLBACK_POLICY",
                    resource_type="POLICY",
                    resource_id=cleaned_id,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={
                        "previous_version": prev_version,
                        "restored_from_version": payload.target_version,
                        "new_version": updated_policy.version,
                    },
                    actor=actor,
                    session=session,
                )
                await session.commit()
                return updated_policy
            else:
                existing = repo.get_by_id(cleaned_id)
                prev_version = existing.version
                updated_fields = existing.model_dump()
                updated_fields.update(update_data)
                updated_fields["version"] = (existing.version or 1) + 1
                updated_policy = Policy(**updated_fields)
                repo._policies[cleaned_id] = updated_policy

                await self._record_version_snapshot(updated_policy, "ROLLBACK", actor, session=None)

                await audit_service.record_event(
                    event_type=AuditEventType.POLICY_ROLLED_BACK,
                    action="ROLLBACK_POLICY",
                    resource_type="POLICY",
                    resource_id=cleaned_id,
                    outcome=AuditOutcome.SUCCESS,
                    metadata={
                        "previous_version": prev_version,
                        "restored_from_version": payload.target_version,
                        "new_version": updated_policy.version,
                    },
                    actor=actor,
                )
                return updated_policy
        finally:
            if session:
                await session.close()


policy_service = PolicyService()
