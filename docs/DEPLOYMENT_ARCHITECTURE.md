# AegisOne — Discovered Deployment Topology & Architecture

This document describes the actual runtime topology, environment configuration, database, and container orchestration discovered in the AegisOne repository.

---

## 1. System Components & Topology

```text
[ Browser / Client Application ]
            │
            ├─────────────────────────────────────────┐
            ▼ (HTTPS / Public API)                    ▼ (HTTPS OIDC / PKCE S256)
┌──────────────────────────────┐          ┌──────────────────────────────┐
│  Frontend Service (Nginx)    │          │  Keycloak Identity Provider  │
│  - React 18 SPA              │          │  - Realm: accessguard        │
│  - Container: Port 3000 -> 80│          │  - Container: Port 8080      │
└──────────────┬───────────────┘          └──────────────┬───────────────┘
               │                                         │
               │ (REST API / JWT)                        │ (RS256 JWKS Verification)
               ▼                                         │
┌──────────────────────────────┐                         │
│  Backend Service (FastAPI)   │ ◄───────────────────────┘
│  - Python 3.13 / Uvicorn     │
│  - Container: Port 8000      │
└──────────────┬───────────────┘
               │
               ├─────────────────────────┐
               ▼ (Asyncpg TCP)           ▼ (SMTP Protocol)
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  PostgreSQL Database         │  │  SMTP Mail Relay Gateway     │
│  - Version: 16 Alpine        │  │  - Port 587 / STARTTLS       │
│  - Container: Port 5432      │  │  - Email OTP MFA Delivery    │
└──────────────────────────────┘  └──────────────────────────────┘
```

---

## 2. Component Technical Stack

| Component | Framework / Technology | Container Image / Base | Config File(s) |
| --- | --- | --- | --- |
| **Frontend** | React 18, Vite, TypeScript, Tailwind | `nginx:alpine` (Multi-stage) | [`frontend/Dockerfile`](file:///y:/hemanth%20projects%201/bava/frontend/Dockerfile), [`frontend/nginx.conf`](file:///y:/hemanth%20projects%201/bava/frontend/nginx.conf) |
| **Backend** | FastAPI, Pydantic v2, SQLAlchemy 2.x | `python:3.13-slim` | [`backend/Dockerfile`](file:///y:/hemanth%20projects%201/bava/backend/Dockerfile), [`backend/app/config.py`](file:///y:/hemanth%20projects%201/bava/backend/app/config.py) |
| **Database** | PostgreSQL 16 Alpine | `postgres:16-alpine` | [`backend/alembic.ini`](file:///y:/hemanth%20projects%201/bava/backend/alembic.ini), [`backend/alembic/env.py`](file:///y:/hemanth%20projects%201/bava/backend/alembic/env.py) |
| **Identity Provider** | Keycloak 24.0.1 (OIDC / PKCE S256) | `quay.io/keycloak/keycloak:24.0.1` | [`keycloak/accessguard-realm.json`](file:///y:/hemanth%20projects%201/bava/keycloak/accessguard-realm.json) |
| **Orchestration** | Docker Compose v3.8 | N/A | [`docker-compose.yml`](file:///y:/hemanth%20projects%201/bava/docker-compose.yml) |

---

## 3. Discovered Network Isolation & Port Binding

- **`postgres`**: Exposed internally on port `5432`. Requires private network binding in production.
- **`keycloak`**: Exposed on port `8080`. Publicly accessible behind TLS reverse proxy.
- **`backend`**: Exposed on port `8000`. Public API router protected by JWT verifier middleware and CORS allowed origins validation.
- **`frontend`**: Nginx web server bound to port `3000` (mapped to internal container port `80`). Serves static SPA bundle with client-side fallback routing (`try_files $uri $uri/ /index.html`).
