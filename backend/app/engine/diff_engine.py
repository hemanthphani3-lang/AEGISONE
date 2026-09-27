from typing import Any
from app.engine.models import FieldDiff, Policy, PolicyDiffResponse


def compute_policy_diff(from_policy: Policy, to_policy: Policy) -> PolicyDiffResponse:
    """Compute field-by-field and collection diffs between two policy versions."""
    changed_fields: list[str] = []
    field_diffs: dict[str, FieldDiff] = {}
    added_collection_items: dict[str, list[Any]] = {}
    removed_collection_items: dict[str, list[Any]] = {}

    # Scalar fields comparison
    scalar_fields = [
        "name",
        "description",
        "enabled",
        "action",
        "target_device_managed",
        "target_device_compliant",
        "target_risk_level",
    ]

    for field in scalar_fields:
        prev_val = getattr(from_policy, field, None)
        new_val = getattr(to_policy, field, None)
        if hasattr(prev_val, "value"):
            prev_val = prev_val.value
        if hasattr(new_val, "value"):
            new_val = new_val.value

        if prev_val != new_val:
            changed_fields.append(field)
            field_diffs[field] = FieldDiff(previous=prev_val, new=new_val)

    # Collection fields comparison
    collection_fields = [
        "target_roles",
        "target_protocols",
        "target_locations",
        "exclusions",
        "excluded_users",
    ]

    for col in collection_fields:
        raw_prev = getattr(from_policy, col, []) or []
        raw_new = getattr(to_policy, col, []) or []

        prev_items = [x.value if hasattr(x, "value") else str(x) for x in raw_prev]
        new_items = [x.value if hasattr(x, "value") else str(x) for x in raw_new]

        added = [item for item in new_items if item not in prev_items]
        removed = [item for item in prev_items if item not in new_items]

        if added:
            added_collection_items[col] = added
            if col not in changed_fields:
                changed_fields.append(col)
        if removed:
            removed_collection_items[col] = removed
            if col not in changed_fields:
                changed_fields.append(col)

    return PolicyDiffResponse(
        policy_id=to_policy.id,
        from_version=from_policy.version,
        to_version=to_policy.version,
        changed_fields=sorted(changed_fields),
        field_diffs=field_diffs,
        added_collection_items=added_collection_items,
        removed_collection_items=removed_collection_items,
    )
