from app.db.models import (
    DBPolicy,
    DBPolicyExcludedUser,
    DBPolicyExclusion,
    DBPolicyTargetLocation,
    DBPolicyTargetProtocol,
    DBPolicyTargetRole,
)
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import Policy


def to_domain_policy(db_policy: DBPolicy) -> Policy:
    """Convert a DBPolicy ORM model instance to a domain Policy model."""
    return Policy(
        id=db_policy.id,
        name=db_policy.name,
        description=db_policy.description,
        enabled=db_policy.enabled,
        action=PolicyDecision(db_policy.action),
        version=getattr(db_policy, "version", 1) or 1,
        target_roles=[UserRole(r.role) for r in db_policy.target_roles],
        target_protocols=[
            AuthProtocol(p.protocol) for p in db_policy.target_protocols
        ],
        target_locations=[l.location for l in db_policy.target_locations],
        target_device_managed=db_policy.target_device_managed,
        target_device_compliant=db_policy.target_device_compliant,
        exclusions=[UserRole(e.role) for e in db_policy.exclusions],
        excluded_users=[u.user_id for u in db_policy.excluded_users],
    )


def from_domain_policy(domain_policy: Policy) -> DBPolicy:
    """Convert a domain Policy model to a DBPolicy ORM model instance."""
    return DBPolicy(
        id=domain_policy.id,
        name=domain_policy.name,
        description=domain_policy.description,
        enabled=domain_policy.enabled,
        action=domain_policy.action.value,
        version=domain_policy.version,
        target_device_managed=domain_policy.target_device_managed,
        target_device_compliant=domain_policy.target_device_compliant,
        target_roles=[
            DBPolicyTargetRole(role=role.value) for role in domain_policy.target_roles
        ],
        target_protocols=[
            DBPolicyTargetProtocol(protocol=proto.value)
            for proto in domain_policy.target_protocols
        ],
        target_locations=[
            DBPolicyTargetLocation(location=loc)
            for loc in domain_policy.target_locations
        ],
        exclusions=[
            DBPolicyExclusion(role=ex.value) for ex in domain_policy.exclusions
        ],
        excluded_users=[
            DBPolicyExcludedUser(user_id=uid)
            for uid in domain_policy.excluded_users
        ],
    )
