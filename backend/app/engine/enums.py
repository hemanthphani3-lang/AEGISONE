from enum import Enum


class UserRole(str, Enum):
    """User roles within the system."""

    STUDENT = "STUDENT"
    STAFF = "STAFF"
    ADMIN = "ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    BREAK_GLASS = "BREAK_GLASS"


class AuthProtocol(str, Enum):
    """Authentication protocols used during sign-in."""

    MODERN = "MODERN"
    LEGACY = "LEGACY"


class PolicyDecision(str, Enum):
    """Possible outcomes of a policy evaluation."""

    ALLOW = "ALLOW"
    MFA_REQUIRED = "MFA_REQUIRED"
    BLOCK = "BLOCK"
