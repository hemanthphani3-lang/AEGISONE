# AEGISONE — SIGNAL PROVIDER & EMAIL OTP MFA IMPLEMENTATION REPORT

**Implementation Date**: September 27, 2026  
**Module Scope**: Extensible Signal Provider Architecture, Geolocation Normalization, Real MFA Completion State, Email OTP Engine & Device Signal Posture.  

---

## 1. SIGNAL PROVIDER ARCHITECTURE

AegisOne features an extensible `SignalProvider` architecture that decouples signal ingestion from policy decision enforcement.

### Provider Abstraction Class Model:
- **`AbstractSignalProvider`**: Abstract base interface producing normalized `SecuritySignal` instances.
- **`KeycloakIdentityProvider`**: Extracts identity claims (`user_id`, `roles`, `auth.mfa_completed`, `auth.protocol`) from Keycloak OIDC tokens.
- **`BrowserLocationProvider`**: Captures and normalizes location payloads from browser Geolocation API (`country`, `region`, `city`).
  - *Location Normalization*: Coarse geographic names are derived without storing or logging raw lat/long coordinates.
  - *Permission Handling*: When location permission is denied by the user, the signal returns `status = UNAVAILABLE` with source `GEOLOCATION_PROVIDER`.
- **`DeviceSignalProvider`**: Evaluates enterprise device posture (`device.managed` and `device.compliant`).
  - *Explicit Unavailable Status*: Returns `status = UNAVAILABLE` with source `DEVICE_PROVIDER` and explanatory metadata (`"NO_DEVICE_MANAGEMENT_PROVIDER"`) instead of falsely reporting `false`.
- **`FutureProviderRegistry`**: Pluggable provider registry for managing third-party signal providers.

---

## 2. EMAIL OTP MFA ENGINE & SMTP INTEGRATION

### Security Architecture & Specifications:
- **Generation**: Cryptographically random 6-digit OTP code generated via `secrets.randbelow(1000000)`.
- **Hashing**: SHA-256 salted hash storage (`hashlib.sha256(salt + code)`). Raw OTP values are never stored, logged, or returned in API responses.
- **Expiration & Limits**:
  - Expiration TTL: 300 seconds (5 minutes).
  - Maximum Verification Attempts: 5.
  - Resend Cooldown: 60 seconds per user session.
  - Invalidation: Generating a new OTP automatically invalidates prior unexpired OTPs.
- **SMTP Email Delivery**:
  - Environment Config: `KC_MAIL_HOST`, `KC_MAIL_PORT`, `KC_MAIL_FROM`, `KC_MAIL_USER`, `KC_MAIL_PASSWORD`.
  - Delivery Fallback: If `KC_MAIL_HOST` is unconfigured, delivery status returns `UNAVAILABLE` with clear administrative messaging.

---

## 3. REAL MFA STATE & POLICY ENFORCEMENT

- **`auth.mfa_completed`**: Distinguishes authenticated session state (`authenticated`) vs verified MFA state (`authenticated + MFA completed`).
- **Policy Precedence**: Evaluator enforces mandatory MFA for administrative roles (`ADMIN`, `SECURITY_ADMIN`).
- **Token Upgrade**: Upon successful OTP verification at `POST /api/v1/auth/mfa/verify-otp`, an upgraded session token with `amr: ["otp"]` and `auth.mfa_completed = true` is issued.
