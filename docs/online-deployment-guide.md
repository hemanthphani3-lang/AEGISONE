# AegisOne — Zero-Cost Online / Public Deployment Guide

This guide details the target **online HTTPS architecture** for deploying **AegisOne** publicly across zero-cost / free-tier infrastructure.

---

## 1. Target Online Architecture Topology

```
                                  INTERNET
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       │                              │                              │
       ▼                              ▼                              ▼
  React App                       Keycloak                        FastAPI
 (Vercel / Netlify)            (Render / Koyeb)             (Render / Fly.io)
  HTTPS                          HTTPS                           HTTPS
       │                              │                               │
       │                              │ OIDC / JWT                    │
       └──────────────────────────────┼──────────────────────────────►│
                                      │                               │
                                      ▼                               ▼
                              Keycloak Internal DB               SQLAlchemy
                             (Supabase / Render DB)                   │
                                                                      ▼
                                                             Supabase PostgreSQL
                                                               (Application DB)
```

---

## 2. Zero-Cost Free-Tier Hosting Strategy Matrix

| Component | Target Provider | Free Tier Specification | Custom HTTPS URL |
| :--- | :--- | :--- | :--- |
| **React Frontend** | Vercel / Netlify | 100 GB/month bandwidth, instant global CDN, automatic SSL | `https://accessguard.vercel.app` |
| **FastAPI Backend** | Render / Koyeb / Fly.io | 512 MB RAM, 0.1 CPU, automatic SSL, continuous Git deploys | `https://accessguard-backend.onrender.com` |
| **Keycloak Identity** | Render / Koyeb | Docker container running `quay.io/keycloak/keycloak:24.0.1`, automatic SSL | `https://aegisone-keycloak.onrender.com` |
| **Keycloak Storage** | Supabase (2nd Project) / Render Postgres | 500 MB free PostgreSQL database for Keycloak internal schema | Host connection string |
| **Application Database**| Supabase PostgreSQL | 500 MB persistent storage, TLS encrypted | `db.yyrvzfkknrbuwcbjmaqc.supabase.co` |

---

## 3. Environment Variable Configuration by Component

### A. React Frontend (Vercel / Netlify Environment Variables)
```ini
VITE_API_BASE_URL=https://accessguard-backend.onrender.com/api/v1
VITE_KEYCLOAK_URL=https://aegisone-keycloak.onrender.com
VITE_KEYCLOAK_REALM=accessguard
VITE_KEYCLOAK_CLIENT_ID=accessguard-frontend
```
*Note: Public client configuration only. Never add database credentials, private keys, or client secrets here.*

### B. FastAPI Backend (Render / Koyeb Environment Variables)
```ini
APP_ENV=production
ALLOWED_ORIGINS=https://accessguard.vercel.app
DATABASE_URL=postgresql+asyncpg://postgres.yyrvzfkknrbuwcbjmaqc:[REDACTED]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
KEYCLOAK_URL=https://aegisone-keycloak.onrender.com
KEYCLOAK_REALM=accessguard
KEYCLOAK_CLIENT_ID=accessguard-backend
KEYCLOAK_CLIENT_SECRET=[REDACTED]
```

---

## 4. Deployment Order & Trust Sequence

1. **Database Schema Verification:** Confirm Supabase PostgreSQL application database is migrated (`alembic upgrade head`).
2. **Keycloak Service Deployment:** Deploy Keycloak container with persistent PostgreSQL backend.
3. **Keycloak OIDC Realm Import:** Import `accessguard` realm with `accessguard-frontend` public client, roles (`ADMIN`, `SECURITY_ADMIN`, `STAFF`, `STUDENT`, `BREAK_GLASS`), and seed test users.
4. **FastAPI Backend Deployment:** Build and deploy `backend/Dockerfile` with `ALLOWED_ORIGINS` bound to the production React URL.
5. **React Frontend Deployment:** Deploy `frontend/` to Vercel/Netlify with production HTTPS environment variables.
6. **End-to-End Verification:** Perform complete authentication flow across external browser/network.

---

## 5. Free-Tier Limitations & Operational Tradeoffs

- **Cold Starts (Render Free Tier):** Web services spin down after 15 minutes of inactivity. First HTTP request after idle takes ~30–50 seconds to boot the container.
- **RAM Constraints:** Free containers provide 512 MB RAM. Keycloak requires minimum ~350 MB RAM in lightweight dev mode (`start-dev`).
- **Storage Persistence:** Keycloak internal state requires an external PostgreSQL database (e.g. separate Supabase database instance) to survive container restarts on ephemeral free hosts.
