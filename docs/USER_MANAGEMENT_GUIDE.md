# AEGISONE — KEYCLOAK USER ACCOUNT MANAGEMENT GUIDE

**Implementation Date**: September 27, 2026  
**Module Scope**: Backend Keycloak Admin REST API integration, User Directory UI, Account Creation & RBAC Role Assignment.  

---

## 1. KEYCLOAK IDENTITY SOURCE ARCHITECTURE

AegisOne maintains Keycloak as the sole authoritative identity store. No user passwords or credentials are stored inside AegisOne's PostgreSQL database.

### Backend-to-Keycloak Administrative Integration:
- **Backend Authorization**: FastAPI backend communicates directly with Keycloak Admin REST API (`/admin/realms/accessguard/users`) using Keycloak master admin credentials.
- **Zero Frontend Secret Leakage**: Keycloak admin credentials and client secrets are never exposed to the browser or frontend source code.

---

## 2. API ENDPOINTS & RBAC RULES

| HTTP Endpoint | Required Permission | Description |
| :--- | :--- | :--- |
| `GET /api/v1/users` | `READ_POLICY` (`ADMIN`, `SECURITY_ADMIN`) | Returns Keycloak realm user directory |
| `POST /api/v1/users` | `WRITE_POLICY` (`ADMIN`, `SECURITY_ADMIN`) | Creates a new user in Keycloak with assigned AegisOne role |
| `POST /api/v1/users/{id}/toggle` | `WRITE_POLICY` (`ADMIN`, `SECURITY_ADMIN`) | Enables or disables a user account |
| `POST /api/v1/users/{id}/reset-password` | `WRITE_POLICY` (`ADMIN`, `SECURITY_ADMIN`) | Resets user password or triggers required-action email |

### Role Creation Rules:
- `ADMIN`: Can create accounts with any role (`ADMIN`, `SECURITY_ADMIN`, `STAFF`, `STUDENT`, `BREAK_GLASS`).
- `SECURITY_ADMIN`: Can create `STAFF` and `STUDENT` accounts, but cannot assign `ADMIN` or `BREAK_GLASS` roles.
- `STAFF` / `STUDENT`: Forbidden from user account creation (`HTTP 403`).

---

## 3. SUPABASE SMTP EMAIL OTP GATEWAY CONFIGURATION

AegisOne integrates with **Supabase SMTP** for delivering 6-digit MFA verification codes to user email inboxes.

### Environment Variables (Server-Side Only)

```env
SUPABASE_SMTP_HOST=smtp.supabase.io
SUPABASE_SMTP_PORT=587
SUPABASE_SMTP_FROM=noreply@accessguard.local
SUPABASE_SMTP_USER=<supabase_smtp_username>
SUPABASE_SMTP_PASSWORD=<supabase_smtp_password>
```

> **Security Note**: All SMTP configuration parameters are strictly backend-only. Plaintext OTP codes and SMTP passwords are never exposed to the frontend or logged in application logs.

