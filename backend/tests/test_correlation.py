import pytest
from app.core.correlation import (
    get_correlation_id,
    set_correlation_id,
    validate_correlation_id,
)


def test_validate_correlation_id_valid() -> None:
    valid_ids = [
        "123e4567-e89b-12d3-a456-426614174000",
        "req-abc-123",
        "correlation_id_99",
    ]
    for cid in valid_ids:
        assert validate_correlation_id(cid) == cid


def test_validate_correlation_id_invalid() -> None:
    invalid_ids = [
        "",
        "   ",
        "a" * 65,  # Exceeds max length
        "req<script>alert(1)</script>",  # Invalid chars
        "cid; DROP TABLE audit_events;",  # SQL injection attempt
    ]
    for cid in invalid_ids:
        assert validate_correlation_id(cid) is None


def test_get_set_correlation_id() -> None:
    test_id = "test-corr-id-123"
    set_correlation_id(test_id)
    assert get_correlation_id() == test_id
