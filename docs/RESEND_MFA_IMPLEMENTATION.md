# AegisOne — Resend Email API MFA Implementation

## 1. Executive Overview

AegisOne MFA email delivery has been upgraded from legacy SMTP transport to the **Resend HTTPS Email API**. This replacement delivers reliable, server-side outbound email delivery for AegisOne's existing 6-digit Email OTP MFA system without altering the core authentication, Keycloak OIDC, PKCE S256, RS256 JWKS validation, RBAC, policy precedence engine, or audit architecture.

---

## 2. System Architecture & Email Transport Flow

```text
User Request / Login
       │
       ▼
Keycloak OIDC + PKCE S256 Authentication
       │
       ▼
AegisOne Policy Engine Evaluation (MFA_REQUIRED)
       │
       ▼
Generate Cryptographically Secure 6-Digit OTP (`secrets.randbelow`)
       │
       ▼
Store Salted SHA-256 OTP Hash (5-min TTL, 60s Cooldown, Max 5 Attempts)
       │
       ▼
Resend Service Abstraction (`app/email/resend_service.py`)
       │
       ▼ (Server-Side Outbound HTTPS POST https://api.resend.com/emails)
Resend HTTPS API Gateway
       │
       ▼
User Inbox (Receives Verification Code)
       │
       ▼
User Enters OTP -> Verify Hashed OTP -> Invalidate OTP -> Upgrade Token
       │
       ▼
`auth.mfa_completed = true` & `amr = ["otp"]` -> Re-evaluate Policy -> ALLOW
```

---

## 3. Server-Only Environment Configuration

Outbound email delivery relies strictly on backend environment variables. The API key is stored server-side and is **never** exposed to the browser or frontend static bundles.

### Backend Configuration (`backend/.env`)

```env
# Server-Only Resend Email API Configuration
RESEND_API_KEY=re_placeholder_xxxxxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev
```

### Backend Config Blueprint (`backend/.env.example`)

```env
# Resend Email API Configuration (Server-Only)
RESEND_API_KEY=
RESEND_FROM_EMAIL=onboarding@resend.dev
```

---

## 4. OTP Security & Cryptographic Controls

The MFA OTP implementation retains all security invariants:

1. **Cryptographic Randomness**: Generated via `secrets.randbelow(1000000)` formatted as a 6-digit string (`000000` to `999999`).
2. **Salted Hash Storage**: Only `sha256(salt + otp_code)` is stored in memory. Plaintext OTP is never persisted or logged.
3. **5-Minute Expiration**: OTP records automatically expire 300 seconds after generation.
4. **60-Second Cooldown**: Enforces a strict 60s cooldown between OTP dispatch requests to prevent spam/abuse.
5. **Attempt Limiting**: Allows a maximum of 5 verification attempts before invalidating the OTP challenge.
6. **Single-Use Invalidation**: Verified OTPs are immediately removed from the active challenge store. Generating a new OTP invalidates any pre-existing OTP for that user.
7. **Session Upgrade**: Upon verification, AegisOne issues an upgraded JWT signed session token with `amr: ["otp"]` and `mfa_completed: True`.

---

## 5. Failure Handling & Secret Protection

- **Missing API Key**: Returns `(False, "UNAVAILABLE", "MFA email delivery is currently unavailable. Please contact an administrator.")` without crashing or exposing stack traces.
- **Provider API Error**: Catches HTTP/network exceptions cleanly. Logs sanitized diagnostic metrics (`logger.error("Resend HTTP API Error code %s", err.code)`) without logging `RESEND_API_KEY`, `Authorization` headers, or OTP plaintext values.
- **Redaction**: `Settings.get_redacted_dict()` automatically redacts `resend.api_key` to `[REDACTED]`.

---

## 6. Testing & Verification Approach

- **Deterministic Unit & Integration Tests**: All automated tests in `backend/tests/test_email_otp_mfa.py` mock the `urllib.request.urlopen` call. Tests execute 100% offline and deterministically without depending on external network availability.
- **Secret Leak Audits**: Automated tests verify that `RESEND_API_KEY`, `Authorization` headers, and plaintext OTPs never leak into log capture buffers or API error outputs.
- **Frontend Build Bundle Scan**: Automated static analysis inspects `frontend/dist` assets to confirm zero exposure of `RESEND_API_KEY` or `re_` keys in client-side bundles.

---

## 7. Local Development & Production Deployment

1. **Local Development**:
   Add `RESEND_API_KEY` and `RESEND_FROM_EMAIL` to `backend/.env`. If omitted, the system gracefully handles unconfigured state with simulated dev notifications.
2. **Production Deployment**:
   Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` as secure environment secrets in the production backend container deployment environment (e.g. Docker / Kubernetes Secrets / Systemd environment file).
