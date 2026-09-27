# AEGISONE — SECURITY & HARDENING MODEL

## 1. Authentication & Real MFA Completion State
- **Protocol**: OpenID Connect (OIDC) / OAuth 2.0 with Authorization Code + PKCE (S256).
- **Signature Algorithm**: RS256 using public key sets served from Keycloak JWKS endpoint (`/protocol/openid-connect/certs`).
- **MFA State**: Distinguishes `authenticated` vs `authenticated + MFA completed` (`auth.mfa_completed`).
- **Email OTP Engine**: 6-digit cryptographically random OTPs, SHA-256 salted hash storage, 5 min TTL, 5 max verification attempts, 60s cooldown, zero plaintext logging. Outbound delivery is executed server-side via the Resend HTTPS Email API (`RESEND_API_KEY`, `RESEND_FROM_EMAIL`). Legacy SMTP delivery has been replaced for AegisOne MFA.

## 2. Authoritative RBAC Model
The system recognizes 5 strictly scoped roles:
- `ADMIN`: Full policy management, user administration, simulation, versioning, rollback, and incident remediation.
- `SECURITY_ADMIN`: User management, policy audit, intelligence inspection, simulation, and incident management.
- `STAFF`: Read-only access to non-sensitive policies and simulation dry-runs.
- `STUDENT`: Restricted access to student-specific resources.
- `BREAK_GLASS`: Emergency read-only access for audited emergency response.

## 3. Signal Safety & Extensibility
- **Geolocation Normalization**: Normalizes locations into country/region/city labels without storing raw lat/long coordinates. Permission denial returns `status = UNAVAILABLE`.
- **Device Signals**: Unconnected device posture signals return `status = UNAVAILABLE` with source `NO_DEVICE_PROVIDER` rather than falsely reporting `false`.

## 4. Decision Precedence
Evaluator enforces a deterministic resolution order:
`BLOCK` > `MFA_REQUIRED` > `ALLOW`

## 5. Credential & Data Protection
- **Log Sanitization**: `sanitize_metadata()` filters all authorization tokens, OTP codes, passwords, secrets, and private keys before writing to audit logs or API outputs.
- **Optimistic Concurrency Control (OCC)**: Prevents race conditions and lost updates using version matching (`expected_version` == `current_version`).
- **Immutable Snapshots**: Policy versions are append-only. Rollback creates a new version (`current_version + 1`) rather than mutating historical records.
