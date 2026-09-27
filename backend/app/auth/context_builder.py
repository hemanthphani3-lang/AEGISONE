from typing import Any
from app.auth.models import AuthenticatedUser
from app.engine.enums import AuthProtocol, UserRole
from app.engine.models import AuthInfo, DeviceInfo, RequestContext


class IdentityContextBuilder:
    """Builder component responsible for converting an AuthenticatedUser principal

    into a clean domain RequestContext for policy evaluation.

    Enforces strict identity anti-spoofing by deriving identity attributes (user_id,
    roles, auth protocol) exclusively from validated identity claims.
    """

    @staticmethod
    def build_context(
        principal: AuthenticatedUser,
        client_data: dict[str, Any] | None = None,
    ) -> RequestContext:
        """Build a domain RequestContext from an AuthenticatedUser.

        Client-supplied identity fields in client_data (e.g. user_id, roles) are strictly ignored.
        """
        # 1. User ID from validated Keycloak subject claim
        user_id = principal.user_id

        # 2. Map recognized Keycloak roles to UserRole enum values
        mapped_roles: list[UserRole] = []
        for role_str in principal.roles:
            try:
                role_enum = UserRole(role_str)
                if role_enum not in mapped_roles:
                    mapped_roles.append(role_enum)
            except ValueError:
                # Safely ignore unrecognized external roles
                pass

        # 3. Authentication protocol (Keycloak/OIDC is always MODERN)
        auth_info = AuthInfo(
            protocol=AuthProtocol.MODERN,
            mfa_completed=principal.mfa_completed,
        )

        # 4. Device context (Unknown by default, not fake booleans)
        device_info = DeviceInfo(managed=None, compliant=None)

        # 5. Location context (Unknown by default)
        location = "UNKNOWN"

        # Safely allow client data ONLY for non-identity context (e.g. device/location) if provided
        if client_data and isinstance(client_data, dict):
            loc_val = client_data.get("location")
            if loc_val and isinstance(loc_val, str):
                location = loc_val.upper()

            dev_val = client_data.get("device")
            if dev_val and isinstance(dev_val, dict):
                managed = dev_val.get("managed")
                compliant = dev_val.get("compliant")
                device_info = DeviceInfo(
                    managed=managed if isinstance(managed, bool) else None,
                    compliant=compliant if isinstance(compliant, bool) else None,
                )

        return RequestContext(
            user_id=user_id,
            roles=mapped_roles,
            location=location,
            device=device_info,
            authentication=auth_info,
        )

    @staticmethod
    def build_security_context(
        principal: AuthenticatedUser,
        client_data: dict[str, Any] | None = None,
    ):
        """Build a normalized SecurityContext using ContextAggregator."""
        from app.signals.aggregator import context_aggregator

        return context_aggregator.aggregate_sync(principal=principal, client_data=client_data)


identity_context_builder = IdentityContextBuilder()

