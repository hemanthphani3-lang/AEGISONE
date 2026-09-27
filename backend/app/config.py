import os
from typing import Any
from urllib.parse import urlparse
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()


class AppConfig(BaseModel):
    """Application metadata and environment configuration."""

    env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    name: str = Field(default="AegisOne")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
            ).split(",")
            if o.strip()
        ]
    )

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "test", "production"}
        lowered = v.lower().strip()
        if lowered not in allowed:
            raise ValueError(
                f"Invalid APP_ENV '{v}'. Allowed values are: {', '.join(sorted(allowed))}"
            )
        return lowered


class DatabaseConfig(BaseModel):
    """Database persistence configuration."""

    url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://accessguard:accessguard_pass@localhost:5432/accessguard_db",
        )
    )

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL cannot be empty.")
        parsed = urlparse(v)
        if not parsed.scheme:
            raise ValueError(
                "DATABASE_URL is missing a valid scheme (e.g. postgresql+asyncpg:// or sqlite://)."
            )
        return v.strip()


class KeycloakConfig(BaseModel):
    """Keycloak OpenID Connect authentication configuration."""

    url: str = Field(
        default_factory=lambda: os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    )
    realm: str = Field(
        default_factory=lambda: os.getenv("KEYCLOAK_REALM", "accessguard")
    )
    client_id: str = Field(
        default_factory=lambda: os.getenv("KEYCLOAK_CLIENT_ID", "accessguard-backend")
    )
    client_secret: str = Field(
        default_factory=lambda: os.getenv(
            "KEYCLOAK_CLIENT_SECRET", "accessguard-secret-dev"
        )
    )

    @field_validator("url")
    @classmethod
    def validate_keycloak_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("KEYCLOAK_URL cannot be empty.")
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                "KEYCLOAK_URL is missing a valid scheme or host (e.g. http://localhost:8080)."
            )
        return v.strip().rstrip("/")


class ExternalServiceConfig(BaseModel):
    """Configuration blueprint for external service credentials and endpoints.

    Establishes the architectural boundary for future integrations without executing API calls.
    """

    service_name: str
    base_url: str
    credential_ref: str = "[REDACTED]"
    timeout_seconds: int = 10


class SupabaseConfig(BaseModel):
    """Supabase project environment configuration blueprint (Server-Only)."""

    url: str | None = Field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    publishable_key: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )
    service_role_key: str | None = Field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )


class ResendConfig(BaseModel):
    """Resend HTTPS Email API server-side configuration."""

    api_key: str | None = Field(default_factory=lambda: os.getenv("RESEND_API_KEY"))
    from_email: str = Field(
        default_factory=lambda: os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    )


class Settings(BaseModel):
    """Central typed settings model for AegisOne."""

    app: AppConfig = Field(default_factory=AppConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    keycloak: KeycloakConfig = Field(default_factory=KeycloakConfig)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    resend: ResendConfig = Field(default_factory=ResendConfig)

    @field_validator("keycloak")
    @classmethod
    def validate_production_secrets(cls, v: KeycloakConfig, info: Any) -> KeycloakConfig:
        # If in production, prevent default fallback secrets
        env_val = os.getenv("APP_ENV", "development").lower().strip()
        if env_val == "production":
            if v.client_secret == "accessguard-secret-dev":
                raise ValueError("Default KEYCLOAK_CLIENT_SECRET cannot be used in production environment.")
        return v

    def get_redacted_dict(self) -> dict[str, Any]:
        """Return a safe representation of configuration with sensitive secrets masked."""
        raw = self.model_dump()

        # Mask sensitive database credentials if present
        db_url = raw.get("db", {}).get("url", "")
        if "@" in db_url:
            parts = db_url.split("@")
            scheme = parts[0].split("://")[0]
            host_db = parts[1]
            raw["db"]["url"] = f"{scheme}://[REDACTED]@{host_db}"
        else:
            raw["db"]["url"] = db_url

        # Mask Keycloak client secret
        if "keycloak" in raw and "client_secret" in raw["keycloak"]:
            raw["keycloak"]["client_secret"] = "[REDACTED]"

        # Mask Supabase keys
        if "supabase" in raw:
            if raw["supabase"].get("publishable_key"):
                raw["supabase"]["publishable_key"] = "[REDACTED]"
            if raw["supabase"].get("service_role_key"):
                raw["supabase"]["service_role_key"] = "[REDACTED]"

        # Mask Resend API key
        if "resend" in raw and raw["resend"].get("api_key"):
            raw["resend"]["api_key"] = "[REDACTED]"

        return raw


def get_settings() -> Settings:
    """Factory function retrieving global validated application settings."""
    return Settings()


# Singleton settings instance
settings = get_settings()

# Backward compatibility & MFA/User configuration exports
APP_ENV = settings.app.env
DATABASE_URL = settings.db.url
KEYCLOAK_URL = settings.keycloak.url
KEYCLOAK_REALM = settings.keycloak.realm
KEYCLOAK_CLIENT_ID = settings.keycloak.client_id
KEYCLOAK_CLIENT_SECRET = settings.keycloak.client_secret
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "accessguard-dev-secret-key-32-bytes-long!")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
KC_MAIL_HOST = os.getenv("KC_MAIL_HOST", "")
KC_MAIL_PORT = os.getenv("KC_MAIL_PORT", "587")
KC_MAIL_FROM = os.getenv("KC_MAIL_FROM", "noreply@accessguard.local")
KC_MAIL_USER = os.getenv("KC_MAIL_USER", "")
KC_MAIL_PASSWORD = os.getenv("KC_MAIL_PASSWORD", "")
SUPABASE_SMTP_HOST = os.getenv("SUPABASE_SMTP_HOST", KC_MAIL_HOST)
SUPABASE_SMTP_PORT = os.getenv("SUPABASE_SMTP_PORT", KC_MAIL_PORT)
SUPABASE_SMTP_FROM = os.getenv("SUPABASE_SMTP_FROM", KC_MAIL_FROM)
SUPABASE_SMTP_USER = os.getenv("SUPABASE_SMTP_USER", KC_MAIL_USER)
SUPABASE_SMTP_PASSWORD = os.getenv("SUPABASE_SMTP_PASSWORD", KC_MAIL_PASSWORD)
KEYCLOAK_ADMIN = os.getenv("KEYCLOAK_ADMIN", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")


