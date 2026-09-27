from typing import Any
import jwt
from jwt import PyJWKClient
from app.auth.models import AuthenticatedUser
from app.config import KEYCLOAK_CLIENT_ID, KEYCLOAK_REALM, KEYCLOAK_URL

KNOWN_ROLES = {"STUDENT", "STAFF", "ADMIN", "SECURITY_ADMIN", "BREAK_GLASS"}


class JWTVerifier:
    """JWT Token verifier for Keycloak OpenID Connect authentication."""

    def __init__(
        self,
        keycloak_url: str = KEYCLOAK_URL,
        realm: str = KEYCLOAK_REALM,
        client_id: str = KEYCLOAK_CLIENT_ID,
        jwk_client: PyJWKClient | None = None,
        signing_key: str | None = None,
    ) -> None:
        self.keycloak_url = keycloak_url.rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.issuer = f"{self.keycloak_url}/realms/{self.realm}"
        self.jwks_uri = f"{self.issuer}/protocol/openid-connect/certs"
        self._jwk_client = jwk_client
        self._signing_key = signing_key

    def get_jwk_client(self) -> PyJWKClient:
        """Get or initialize PyJWKClient for fetching live Keycloak JWKS."""
        if self._jwk_client is None:
            self._jwk_client = PyJWKClient(self.jwks_uri)
        return self._jwk_client

    def verify_token(self, token: str) -> AuthenticatedUser:
        """Verify JWT token signature, issuer, expiration, and parse claims.

        Raises ValueError or Exception on validation failure.
        """
        if not token or not isinstance(token, str):
            raise ValueError("Token is missing or invalid.")

        # Determine signing key (from test override or live JWKS client)
        if self._signing_key is not None:
            key = self._signing_key
        else:
            try:
                jwk_client = self.get_jwk_client()
                signing_key_obj = jwk_client.get_signing_key_from_jwt(token)
                key = signing_key_obj.key
            except Exception as exc:
                raise ValueError(f"Unable to retrieve signing key: {exc}") from exc

        # Decode and strictly validate signature, issuer, and expiration
        from app.config import APP_ENV
        allowed_algs = ["RS256"] if APP_ENV == "production" else ["RS256", "HS256"]
        
        try:
            # Inspect token payload without verification first to check aud claim presence
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            token_aud = unverified_claims.get("aud")
            verify_aud_flag = True if token_aud is not None else False

            decode_kwargs = {
                "key": key,
                "algorithms": allowed_algs,
                "options": {
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": verify_aud_flag,
                },
                "issuer": self.issuer,
            }
            if verify_aud_flag:
                decode_kwargs["audience"] = [self.client_id, "account"]

            payload: dict[str, Any] = jwt.decode(token, **decode_kwargs)
        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Token has expired.") from exc
        except jwt.InvalidIssuerError as exc:
            raise ValueError(f"Invalid issuer in token. Expected: {self.issuer}") from exc
        except jwt.InvalidAudienceError as exc:
            raise ValueError(f"Invalid audience in token: {exc}") from exc
        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token: {exc}") from exc

        # Extract user_id and username
        user_id = payload.get("sub") or payload.get("preferred_username")
        username = payload.get("preferred_username") or user_id

        if not user_id or not username:
            raise ValueError("Token payload missing user identity claims.")

        # Extract roles from realm_access or resource_access
        extracted_roles: set[str] = set()

        realm_access = payload.get("realm_access", {})
        if isinstance(realm_access, dict):
            for role in realm_access.get("roles", []):
                if role in KNOWN_ROLES:
                    extracted_roles.add(role)

        resource_access = payload.get("resource_access", {})
        if isinstance(resource_access, dict):
            client_access = resource_access.get(self.client_id, {})
            if isinstance(client_access, dict):
                for role in client_access.get("roles", []):
                    if role in KNOWN_ROLES:
                        extracted_roles.add(role)

        direct_roles = payload.get("roles", [])
        if isinstance(direct_roles, list):
            for role in direct_roles:
                if role in KNOWN_ROLES:
                    extracted_roles.add(role)

        # Inspect MFA claims
        mfa_completed = False
        amr_claim = payload.get("amr", [])
        amr_list: list[str] = []
        if isinstance(amr_claim, list):
            amr_list = [str(x) for x in amr_claim]
            mfa_indicators = {"otp", "mfa", "duo", "fido", "hwk"}
            if any(str(indicator).lower() in mfa_indicators for indicator in amr_claim):
                mfa_completed = True

        acr_claim = payload.get("acr")
        if acr_claim in {"2", "3", "mfa"}:
            mfa_completed = True

        return AuthenticatedUser(
            user_id=str(user_id),
            username=str(username),
            roles=sorted(list(extracted_roles)),
            mfa_completed=mfa_completed,
            amr=amr_list,
        )


# Global default verifier instance
jwt_verifier = JWTVerifier()
