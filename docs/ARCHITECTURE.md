# AEGISONE — SYSTEM ARCHITECTURE DOCUMENTATION

## 1. Overview
AegisOne is a Zero-Trust Policy Management, Real-time Evaluation, Extensible Signal Provider Engine, Policy Intelligence, and SOC Incident Remediation platform.

## 2. Key Architecture Components
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons.
- **Backend API**: FastAPI (Python 3.12+) running async ASGI workers.
- **Identity & Authentication**: Keycloak OpenID Connect with PKCE S256 & RS256 JWKS verification.
- **Signal Provider Architecture**: Extensible `SignalProvider` abstraction (`KeycloakSignalProvider`, `BrowserLocationProvider`, `DeviceSignalProvider`, `FutureProviderRegistry`).
- **MFA Engine**: Email OTP MFA with SHA-256 salted hash verification, 60s resend cooldown, 5 min TTL, and SMTP delivery.
- **User Administration**: Keycloak-backed user management via backend Admin REST integration.
- **Database Layer**: PostgreSQL 16 managed via AsyncSQLAlchemy 2.0 and Alembic migrations.
- **Policy Engine**: Centralized, deterministic evaluation pipeline with precedence `BLOCK` > `MFA_REQUIRED` > `ALLOW`.
- **Policy Intelligence & SOC**: Automated risk detection (shadowing, conflicts, lockout risk) with integrated SOC incident lifecycle state machines.

## 3. Data Flow
1. User logs in via Keycloak OIDC PKCE flow to acquire RS256 signed JWTs.
2. Signal Provider Engine collects signals from Keycloak identity claims, Browser Geolocation API, and Device Posture providers.
3. If policy requires MFA, Email OTP challenge is dispatched via `POST /api/v1/auth/mfa/send-otp`. Upon verification, session upgrades to `auth.mfa_completed = true`.
4. Policy Evaluation evaluates active rules sequentially and resolves final decision deterministically.
5. All mutations produce immutable `PolicyVersion` records and trigger sanitized `AuditEvent` entries.
