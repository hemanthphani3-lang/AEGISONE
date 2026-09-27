import pytest
from app.config import (
    AppConfig,
    DatabaseConfig,
    ExternalServiceConfig,
    KeycloakConfig,
    Settings,
    get_settings,
)
from app.integrations.base import AbstractExternalProvider


def test_valid_default_settings():
    """Verify default Settings initialization."""
    settings = get_settings()
    assert settings.app.env in {"development", "test", "production"}
    assert settings.app.name == "AegisOne"
    assert "accessguard" in settings.db.url or "postgres" in settings.db.url
    assert settings.keycloak.realm == "accessguard"


def test_invalid_app_env_raises_value_error():
    """Verify invalid APP_ENV raises ValueError."""
    with pytest.raises(ValueError, match="Invalid APP_ENV"):
        AppConfig(env="super_env")


def test_invalid_database_url_raises_value_error():
    """Verify empty or missing scheme in DATABASE_URL raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        DatabaseConfig(url="")

    with pytest.raises(ValueError, match="missing a valid scheme"):
        DatabaseConfig(url="invalid_no_scheme_path")


def test_invalid_keycloak_url_raises_value_error():
    """Verify invalid KEYCLOAK_URL raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        KeycloakConfig(url="")

    with pytest.raises(ValueError, match="missing a valid scheme or host"):
        KeycloakConfig(url="not_a_url")


def test_secret_redaction():
    """Verify get_redacted_dict masks sensitive credentials in DATABASE_URL and KEYCLOAK_CLIENT_SECRET."""
    settings = Settings(
        db=DatabaseConfig(
            url="postgresql+asyncpg://admin_user:secret_password@localhost:5432/my_db"
        ),
        keycloak=KeycloakConfig(
            client_secret="top_secret_keycloak_secret"
        ),
    )
    redacted = settings.get_redacted_dict()

    # Verify database secret masked
    assert "secret_password" not in redacted["db"]["url"]
    assert "admin_user" not in redacted["db"]["url"]
    assert "[REDACTED]" in redacted["db"]["url"]

    # Verify keycloak client secret masked
    assert redacted["keycloak"]["client_secret"] == "[REDACTED]"
    assert "top_secret_keycloak_secret" not in str(redacted)


def test_external_integration_boundary():
    """Verify ExternalServiceConfig and AbstractExternalProvider abstraction."""
    ext_config = ExternalServiceConfig(
        service_name="MockNotificationService",
        base_url="https://api.mockservice.internal/v1",
        credential_ref="vault://secret/mock-service-key",
    )

    class MockProvider(AbstractExternalProvider):
        def is_configured(self) -> bool:
            return bool(self.config.base_url and self.config.credential_ref)

    provider = MockProvider(ext_config)
    assert provider.service_name == "MockNotificationService"
    assert provider.is_configured() is True
