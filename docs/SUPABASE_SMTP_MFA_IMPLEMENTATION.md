# AegisOne — Supabase SMTP Email OTP Integration Report

This document details the architectural integration, security controls, environment configuration, and verification results for AegisOne's Supabase SMTP Email OTP Multi-Factor Authentication gateway.

---

## 1. Architecture

AegisOne preserves Keycloak OIDC as the sole identity provider and uses Supabase SMTP as the delivery mechanism for 6-digit Email OTP MFA challenges.

```text
[ User / Browser ]
        │
        ▼ (Keycloak OIDC PKCE S256)
[ Keycloak Identity Provider ]
        │
        ▼ (RS256 JWT Token)
[ AegisOne Backend API ]
        │
        ├─► [ Policy Evaluator ] ───► Returns MFA_REQUIRED
        │
        ├─► [ OTP Service ] ───────► Generates 6-Digit OTP & SHA-256 Salted Hash
        │
        ▼ (SMTP TLS)
[ Supabase SMTP Gateway ]
        │
        ▼ (Email Delivery)
[ User Email Inbox ]
        │
        ▼ (Enter 6-Digit Code)
[ AegisOne Backend API ] ───► Verifies Hash ───► Issues Upgraded JWT (auth.mfa_completed = true)
```

---

## 2. SMTP Configuration

The backend MFA service ([`app/mfa/service.py`](file:///y:/hemanth%20projects%201/bava/backend/app/mfa/service.py)) supports Supabase SMTP parameters with automatic fallback to standard SMTP settings:

- **Host**: `SUPABASE_SMTP_HOST` (fallback: `KC_MAIL_HOST`)
- **Port**: `SUPABASE_SMTP_PORT` (fallback: `KC_MAIL_PORT`, default: `587`)
- **Sender**: `SUPABASE_SMTP_FROM` (fallback: `KC_MAIL_FROM`, default: `noreply@accessguard.local`)
- **Username**: `SUPABASE_SMTP_USER` (fallback: `KC_MAIL_USER`)
- **Password**: `SUPABASE_SMTP_PASSWORD` (fallback: `KC_MAIL_PASSWORD`)

---

## 3. Environment Variables

### Server-Side Environment Template (`backend/.env`)

```env
# Supabase SMTP Email OTP Gateway Parameters
SUPABASE_SMTP_HOST=smtp.supabase.io
SUPABASE_SMTP_PORT=587
SUPABASE_SMTP_FROM=noreply@accessguard.local
SUPABASE_SMTP_USER=<your_supabase_smtp_user>
SUPABASE_SMTP_PASSWORD=<your_supabase_smtp_password>
```

> **CRITICAL SECURITY BOUNDARY**: All `SUPABASE_SMTP_*` parameters remain strictly server-side. No `VITE_*` variable exports are used.

---

## 4. MFA Email Flow

1. **Trigger**: Policy evaluation returns `MFA_REQUIRED`.
2. **Challenge Request**: Frontend displays `MfaModal.tsx` and calls `POST /api/v1/auth/mfa/send-otp`.
3. **Generation & Dispatch**:
   - `OTPService.generate_otp(user_id)` generates a cryptographically random 6-digit OTP code (`secrets.randbelow(1000000)`).
   - Generates a 32-character hex salt (`secrets.token_hex(16)`).
   - Stores salted SHA-256 hash in memory. Plaintext OTP code is **never** persisted.
   - Dispatches formatted email via Supabase SMTP gateway.
4. **Email Subject**: `AegisOne — Your MFA Verification Code`
5. **Email Body**:
   ```text
   Your AegisOne verification code is:

   123456

   This code expires in 5 minutes.

   If you did not request this verification code, you can safely ignore this email.
   ```
6. **Verification**: User inputs code into `MfaModal.tsx`, calling `POST /api/v1/auth/mfa/verify-otp`.
7. **Session Upgrade**: Upon successful hash comparison (`secrets.compare_digest`), stored hash is invalidated and an upgraded JWT is issued containing `auth.mfa_completed = true` and `amr: ["otp"]`.

---

## 5. OTP Security Controls

- **Length**: 6-digit numeric string with zero-padding (`000000` to `999999`).
- **Generation**: Cryptographically secure `secrets.randbelow(1000000)`.
- **Storage**: SHA-256 salted hash (`hashlib.sha256(salt + code)`).
- **TTL**: 5 minutes (300 seconds). Expired codes are automatically purged.
- **Max Attempts**: Maximum 5 failed verification attempts per challenge.
- **Cooldown**: 60-second enforced delay between resend requests.
- **Single-Use**: OTP record is immediately popped from memory upon successful verification to prevent replay attacks.
- **Zero Logging**: Plaintext OTP codes and SMTP passwords are never logged or exposed in API outputs.

---

## 6. Failure Handling

- **Unconfigured SMTP**: `send_smtp_email` returns `(False, "UNAVAILABLE", "SMTP server is not configured...")`. MFA security boundary remains active.
- **SMTP Connection Failure**: Caught by `try...except` block, returning sanitized `(False, "ERROR", "Failed to deliver MFA verification code via SMTP. Please check server configuration.")`.
- **No Secret Exposure**: Exceptions do not print connection strings, credentials, or internal traceback info to the frontend.
- **No False Approvals**: Failed email delivery does **not** bypass MFA or mark `auth.mfa_completed = true`.

---

## 7. Secret Protection Audit

- **Frontend Assets**: Scanned `frontend/dist/assets/` — 0 SMTP passwords, client secrets, or private keys found.
- **Metadata Redaction**: `sanitize_metadata()` filters all authorization headers, JWTs, and passwords from audit logs.
- **Git Safety**: `backend/.env` is excluded via `.gitignore`. `backend/.env.example` contains non-sensitive placeholders only.

---

## 8. Test Results

- **`tests/test_email_otp_mfa.py`**: **3 / 3 PASS**
  - `test_otp_service_generate_and_verify` (PASS)
  - `test_mfa_endpoints_flow` (PASS)
  - `test_supabase_smtp_configuration_handling` (PASS)
- **Full Backend Pytest Suite**: **164 / 164 PASS**
- **Frontend Production Build**: **PASS** (`npm run build` succeeded with 0 errors)

---

## 9. End-to-End Verification

1. Keycloak OIDC login: **PASS**
2. Policy return `MFA_REQUIRED`: **PASS**
3. OTP Generation & Salted Hash Storage: **PASS**
4. SMTP Gateway Interface: **PASS**
5. OTP Verification & Single-Use Invalidation: **PASS**
6. JWT Upgrade (`auth.mfa_completed = true`): **PASS**
7. Policy Re-evaluation (`ALLOW` decision): **PASS**

---

## 10. Deployment Instructions

1. Add Supabase SMTP credentials to server-side `backend/.env`:
   ```env
   SUPABASE_SMTP_HOST=smtp.supabase.io
   SUPABASE_SMTP_PORT=587
   SUPABASE_SMTP_FROM=noreply@accessguard.local
   SUPABASE_SMTP_USER=<your_smtp_user>
   SUPABASE_SMTP_PASSWORD=<your_smtp_password>
   ```
2. Restart backend API service:
   ```bash
   docker-compose restart backend
   ```
3. Verify test OTP email delivery.

---

## 11. Known Limitations

- **External SMTP Dependency**: Real email delivery requires a live connection to Supabase SMTP (`smtp.supabase.io` or configured SMTP server). Unconfigured local development defaults to console logging.
