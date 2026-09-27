# AegisOne — Production Deployment & Configuration Guide

This guide outlines the production deployment topology, mandatory environment variables, Keycloak realm settings, and security controls for deploying AegisOne outside `localhost`.

---

## 1. System Topology Architecture

```text
[ Browser / Client ]
       │
       ├─────────────────────────────────┐
       ▼ (HTTPS)                         ▼ (HTTPS OIDC / PKCE S256)
[ Production Frontend (Nginx) ]   [ Keycloak Identity Provider ]
       │                                 │
       │ (REST / Bearer JWT)             │ (JWKS RS256 Validation)
       ▼                                 │
[ Production Backend (FastAPI) ] ◄───────┘
       │
       ├────────────────────────┐
       ▼                        ▼
[ PostgreSQL DB ]        [ SMTP Mail Server ]
```

---

## 2. Required Environment Variables

### A. Backend Server Environment Variables (`backend/.env`)

```env
# Production Environment Flag
APP_ENV=production
APP_DEBUG=false

# Allowed Frontend Origins for CORS (Comma-separated)
ALLOWED_ORIGINS=https://accessguard.domain.com

# PostgreSQL Connection String (Asyncpg driver)
DATABASE_URL=postgresql+asyncpg://<db_user>:<db_password>@<db_host>:5432/<db_name>

# Keycloak OIDC Provider Configuration
KEYCLOAK_URL=https://auth.domain.com
KEYCLOAK_REALM=accessguard
KEYCLOAK_CLIENT_ID=accessguard-backend
KEYCLOAK_CLIENT_SECRET=<production-client-secret>

# Keycloak Admin Credentials (For User Directory Management)
KEYCLOAK_ADMIN=<admin_username>
KEYCLOAK_ADMIN_PASSWORD=<admin_password>

# Resend Email API Server-Side Configuration (For AegisOne MFA OTP Delivery)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=onboarding@resend.dev

# JWT Verification Key (Fallback secret if RS256 JWKS unreachable)
JWT_SECRET_KEY=<strong-32-byte-secret>

```

### B. Frontend Public Environment Variables (`frontend/.env`)

> **IMPORTANT**: `VITE_*` environment variables are bundled directly into browser static assets at build time. Never place private keys or administrative passwords in frontend environment variables.

```env
VITE_API_BASE_URL=https://api.accessguard.domain.com/api/v1
VITE_KEYCLOAK_URL=https://auth.domain.com
VITE_KEYCLOAK_REALM=accessguard
VITE_KEYCLOAK_CLIENT_ID=accessguard-frontend
```

---

## 3. Keycloak Production Realm & Client Configuration

1. **Realm Settings**:
   - **Name**: `accessguard`
   - **Require SSL**: `all` (Forces HTTPS on all endpoints)
2. **Frontend Public Client (`accessguard-frontend`)**:
   - **Client Protocol**: `openid-connect`
   - **Access Type**: `public`
   - **Standard Flow**: `Enabled`
   - **Implicit Flow**: `Disabled`
   - **Direct Access Grants**: `Disabled`
   - **PKCE Code Challenge Method**: `S256`
   - **Valid Redirect URIs**: `https://accessguard.domain.com/*`
   - **Web Origins**: `https://accessguard.domain.com`
   - **Post Logout Redirect URIs**: `https://accessguard.domain.com/login`
3. **Backend Confidential Client (`accessguard-backend`)**:
   - **Access Type**: `confidential` (Client Secret required)
   - **Service Accounts Enabled**: `Enabled`
   - **Direct Access Grants**: `Disabled`

---

## 4. Production Deployment Order

Execute deployment steps in the following sequence:

1. **Database Tier**: Provision PostgreSQL instance and create database `accessguard_db`.
2. **Identity Tier**: Deploy Keycloak, import/configure `accessguard` realm, and apply SSL certificates.
3. **Backend Tier**:
   - Deploy FastAPI container.
   - Run Alembic database migrations to bring database schema to head:
     ```bash
     alembic upgrade head
     ```
4. **Email Gateway**: Configure Resend Email API environment variables (`RESEND_API_KEY`, `RESEND_FROM_EMAIL`) for server-side Email OTP MFA delivery (SMTP legacy transport is no longer used).
5. **Frontend Tier**: Build static bundle with production `VITE_*` values and deploy under Nginx:
   ```bash
   npm run build
   ```
6. **Verification**: Perform automated smoke test verifying end-to-end OIDC authentication, policy evaluation, Email OTP MFA, and incident response.
