from typing import Any
from app.engine.enums import AuthProtocol, PolicyDecision, UserRole
from app.engine.models import PolicyCreate, PolicyUpdate, PolicyValidationResponse


VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}


def validate_policy_definition(
    data: dict[str, Any] | PolicyCreate | PolicyUpdate | Any,
    is_create: bool = False,
) -> PolicyValidationResponse:
    """Centralized server-side policy validation and safety analysis layer.

    Validates field correctness, enum values, structural integrity, and potential safety risks.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Extract dictionary payload
    if hasattr(data, "model_dump"):
        raw = data.model_dump(exclude_unset=True)
    elif isinstance(data, dict):
        raw = dict(data)
    else:
        raw = {}

    # 1. Basic Fields Validation
    if is_create:
        policy_id = raw.get("id")
        if not policy_id or not str(policy_id).strip():
            errors.append("Policy ID is required and cannot be empty.")
        elif not isinstance(policy_id, str):
            errors.append("Policy ID must be a string.")

    if "name" in raw or is_create:
        name = raw.get("name")
        if name is None or not str(name).strip():
            errors.append("Policy name cannot be empty or whitespace.")

    if "description" in raw or is_create:
        description = raw.get("description")
        if description is None or not str(description).strip():
            errors.append("Policy description cannot be empty or whitespace.")

    if "action" in raw or is_create:
        action_val = raw.get("action")
        if action_val is None:
            errors.append("Policy action is required.")
        else:
            action_str = action_val.value if isinstance(action_val, PolicyDecision) else str(action_val)
            if action_str not in PolicyDecision._value2member_map_:
                errors.append(f"Invalid policy action '{action_str}'. Must be one of: ALLOW, MFA_REQUIRED, BLOCK.")

    # 2. Target Roles Validation
    target_roles_raw = raw.get("target_roles")
    target_roles_set = set()
    if target_roles_raw is not None:
        if not isinstance(target_roles_raw, list):
            errors.append("target_roles must be a list.")
        else:
            for item in target_roles_raw:
                val = item.value if isinstance(item, UserRole) else str(item)
                if val not in UserRole._value2member_map_:
                    errors.append(f"Invalid target role '{val}'. Supported roles: {[r.value for r in UserRole]}.")
                else:
                    target_roles_set.add(val)

    # 3. Target Protocols Validation
    target_protocols_raw = raw.get("target_protocols")
    if target_protocols_raw is not None:
        if not isinstance(target_protocols_raw, list):
            errors.append("target_protocols must be a list.")
        else:
            for item in target_protocols_raw:
                val = item.value if isinstance(item, AuthProtocol) else str(item)
                if val not in AuthProtocol._value2member_map_:
                    errors.append(f"Invalid target protocol '{val}'. Supported protocols: MODERN, LEGACY.")

    # 4. Target Risk Level Validation
    target_risk = raw.get("target_risk_level")
    if target_risk is not None and target_risk != "":
        risk_str = str(target_risk).upper()
        if risk_str not in VALID_RISK_LEVELS:
            errors.append(f"Invalid target risk level '{target_risk}'. Supported levels: {sorted(list(VALID_RISK_LEVELS))}.")

    # 5. Exclusions Validation
    exclusions_raw = raw.get("exclusions")
    exclusions_set = set()
    if exclusions_raw is not None:
        if not isinstance(exclusions_raw, list):
            errors.append("exclusions must be a list.")
        else:
            for item in exclusions_raw:
                val = item.value if isinstance(item, UserRole) else str(item)
                if val not in UserRole._value2member_map_:
                    errors.append(f"Invalid excluded role '{val}'. Supported roles: {[r.value for r in UserRole]}.")
                else:
                    exclusions_set.add(val)

    excluded_users_raw = raw.get("excluded_users")
    if excluded_users_raw is not None and not isinstance(excluded_users_raw, list):
        errors.append("excluded_users must be a list of user ID strings.")

    # 6. Safety Checks & Warnings
    # Check for empty target scope
    has_target_roles = bool(target_roles_raw)
    has_target_protocols = bool(target_protocols_raw)
    has_target_locations = bool(raw.get("target_locations"))
    has_target_risk = bool(target_risk)
    has_device = raw.get("target_device_managed") is not None or raw.get("target_device_compliant") is not None

    if not (has_target_roles or has_target_protocols or has_target_locations or has_target_risk or has_device):
        warnings.append("Policy has an empty target scope. It will apply unconditionally to ALL incoming requests.")

    # Check for conflicting role targets and exclusions
    overlap = target_roles_set.intersection(exclusions_set)
    if overlap:
        errors.append(f"Conflict detected: Role(s) {sorted(list(overlap))} cannot be both targeted and excluded.")

    valid = len(errors) == 0
    return PolicyValidationResponse(valid=valid, warnings=warnings, errors=errors)
