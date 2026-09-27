import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.models import AuthenticatedUser
from app.db.converters import to_domain_policy
from app.db.models import DBPolicy
from app.engine.intelligence import policy_intelligence_engine
from app.engine.intelligence_models import FindingSeverity
from app.incidents.models import IncidentCreate, IncidentSeverity, IncidentStatus
from app.incidents.repository import incident_repository
from app.incidents.service import incident_service


class IntelligenceIncidentPipeline:
    """Automated intelligence scan pipeline mapping static security findings to deduplicated incident records."""

    @staticmethod
    def generate_fingerprint(finding_type: str, policy_id: str | None, reason: str) -> str:
        raw_str = f"{finding_type}:{policy_id or 'global'}:{reason.strip()}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:32]

    async def sync_intelligence_incidents(
        self,
        db: AsyncSession,
        actor: AuthenticatedUser | str = "SYSTEM_INTELLIGENCE_PIPELINE",
        correlation_id: str = "SYSTEM_SYNC",
    ) -> list[str]:
        """Runs static analysis over all enabled policies and creates incidents for HIGH/CRITICAL findings."""
        stmt = select(DBPolicy).options(
            selectinload(DBPolicy.target_roles),
            selectinload(DBPolicy.target_protocols),
            selectinload(DBPolicy.target_locations),
            selectinload(DBPolicy.exclusions),
            selectinload(DBPolicy.excluded_users),
        )
        res = await db.scalars(stmt)
        db_policies = list(res.all())
        policies = [to_domain_policy(p) for p in db_policies]
        report = policy_intelligence_engine.analyze_all(policies)

        created_incident_ids: list[str] = []

        for finding in report.global_findings:
            if finding.severity not in {FindingSeverity.HIGH, FindingSeverity.CRITICAL}:
                continue

            policy_id = finding.affected_policy_ids[0] if finding.affected_policy_ids else None
            fingerprint = self.generate_fingerprint(finding.finding_type, policy_id, finding.reason)

            existing = await incident_repository.get_active_incident_by_fingerprint(db, fingerprint)
            if existing:
                continue

            sev = IncidentSeverity.CRITICAL if finding.severity == FindingSeverity.CRITICAL else IncidentSeverity.HIGH

            create_payload = IncidentCreate(
                title=f"[{finding.severity.value}] {finding.finding_type}: {finding.reason[:100]}",
                description=f"{finding.reason}\n\nRecommended Remediation: {finding.recommendation}",
                severity=sev,
                status=IncidentStatus.OPEN,
                source_type="INTELLIGENCE_FINDING",
                source_id=finding.finding_type,
                policy_id=policy_id,
                finding_id=finding.finding_type,
                fingerprint=fingerprint,
                assigned_to=None,
            )

            created_inc = await incident_service.create_incident(
                db=db,
                data=create_payload,
                actor=actor,
                correlation_id=correlation_id,
            )
            created_incident_ids.append(created_inc.id)

        return created_incident_ids


intelligence_incident_pipeline = IntelligenceIncidentPipeline()
