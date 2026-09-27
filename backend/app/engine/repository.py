from abc import ABC, abstractmethod
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import Policy

DEFAULT_POLICIES: list[Policy] = [
    Policy(
        id="admin-mfa",
        name="Require MFA for Administrators",
        description="Administrators must complete MFA.",
        enabled=True,
        target_roles=[UserRole.ADMIN, UserRole.SECURITY_ADMIN],
        target_protocols=[],
        action=PolicyDecision.MFA_REQUIRED,
        exclusions=[UserRole.BREAK_GLASS],
        excluded_users=[],
    ),
    Policy(
        id="block-legacy-auth",
        name="Block Legacy Authentication",
        description="Legacy authentication protocols are blocked.",
        enabled=True,
        target_roles=[],
        target_protocols=[AuthProtocol.LEGACY],
        action=PolicyDecision.BLOCK,
        exclusions=[],
        excluded_users=[],
    ),
]


class AbstractPolicyRepository(ABC):
    """Abstract interface for policy repositories.

    Allows PolicyEvaluator to be decoupled from specific persistence layers.
    """

    @abstractmethod
    def get_all(self) -> list[Policy]:
        """Retrieve all active policies."""
        pass

    @abstractmethod
    def get_by_id(self, policy_id: str) -> Policy | None:
        """Retrieve a policy by its ID."""
        pass


class InMemoryPolicyRepository(AbstractPolicyRepository):
    """In-memory repository for policy storage and retrieval.

    Validates that policy IDs are unique during initialization.
    """

    def __init__(self, policies: list[Policy] | None = None) -> None:
        source_policies = policies if policies is not None else DEFAULT_POLICIES
        self._policies: dict[str, Policy] = {}
        self._history: dict[str, list[dict]] = {}
        for policy in source_policies:
            if policy.id in self._policies:
                raise ValueError(f"Duplicate policy ID detected: '{policy.id}'")
            self._policies[policy.id] = policy

    def get_all(self) -> list[Policy]:
        """Retrieve all registered policies."""
        return list(self._policies.values())

    def get_by_id(self, policy_id: str) -> Policy | None:
        """Retrieve a single policy by ID, or None if not found."""
        return self._policies.get(policy_id)


# Backward compatibility alias
PolicyRepository = InMemoryPolicyRepository

# Global singleton instance for in-memory policies
policy_repository = InMemoryPolicyRepository()
