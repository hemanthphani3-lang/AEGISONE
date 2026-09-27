# AegisOne — Zero-Cost Conditional Access Policy Lab & Simulator

AegisOne is a zero-cost Conditional Access Policy Lab / Simulator designed to simulate, test, evaluate, and audit zero-trust security policies and conditional access evaluation.

> **Important Architecture Principle**: Frontend authorization is a user-experience layer; backend authorization is the authoritative security boundary.

---

## Architecture Overview

```
                ┌───────────────┐
                │   Keycloak    │
                └───────┬───────┘
                        │
                        ▼
                 Authentication
                        │
                        ▼
┌─────────────────────────────────────────────┐
│                  FRONTEND                   │
│  React + TypeScript + Vite + Tailwind CSS   │
│                                             │
│  Router → Layout → Features → API Client    │
│                         │                   │
│                         ▼                   │
│                    UI State                 │
└─────────────────────────┬───────────────────┘
                          │
                          │ HTTPS / REST API
                          ▼
┌─────────────────────────────────────────────┐
│                  BACKEND                    │
│             FastAPI + Python                │
│                                             │
│ Authentication (JWT Verifier)               │
│      ↓                                      │
│ Authorization (RBAC)                        │
│      ↓                                      │
│ Domain Services                             │
│      ↓                                      │
│ Risk Engine / Policy Evaluator / Simulation │
│      ↓                                      │
│ PostgreSQL Database                         │
└─────────────────────────────────────────────┘
```

---

## Frontend Architecture (Iteration 13)

### Structure & Framework
- **Core Stack**: React 19, TypeScript, Vite, Tailwind CSS v4.
- **Directory Hierarchy**:
  - `src/app/`: Configuration (`env.ts`), Providers (`AuthProvider.tsx`, `ToastProvider.tsx`), Router (`AppRouter.tsx`, `ProtectedRoute.tsx`).
  - `src/components/`: Modular UI design system (`Button`, `Card`, `Badge`, `Skeleton`, `EmptyState`, `ErrorState`), Layout shell (`Header`, `Sidebar`, `AppShell`), Common utilities (`HealthBadge`, `ToastContainer`).
  - `src/services/`:
    - `auth/keycloakService.ts`: PKCE OIDC authentication wrapper with automatic token refresh.
    - `api/apiClient.ts`: Centralized HTTP client attaching Bearer tokens, correlation IDs (`X-Correlation-ID`), and normalized error handling (`ApiError`).
    - Feature APIs: `policyApi.ts`, `evaluationApi.ts`, `auditApi.ts`, `simulationApi.ts`, `healthApi.ts`.
  - `src/features/`: Feature modules (`auth`, `dashboard`, `policies`, `evaluation`, `audit`, `simulation`).
  - `src/types/`: TypeScript definitions strictly aligned with backend Pydantic models.

### Environment & Security Boundaries
- **Variables**: `VITE_API_BASE_URL`, `VITE_KEYCLOAK_URL`, `VITE_KEYCLOAK_REALM`, `VITE_KEYCLOAK_CLIENT_ID`.
- **Secret Safety**: Frontend environment variables contain NO secrets (no passwords, signing keys, client secrets, or private keys).
- **Backend Authority**: Frontend role checks (`ADMIN`, `SECURITY_ADMIN`, `STAFF`, `STUDENT`) govern UI display only. Backend endpoints strictly enforce RBAC.
- **No Fake Data**: The security dashboard displays real backend connection status (`/health`) and authenticated Keycloak principal data. No synthetic security scores or fake threat counters exist.

---

## Local Setup & Development

### 1. Backend & Infrastructure
```bash
# Start PostgreSQL & Keycloak containers
docker-compose up -d

# Run backend (FastAPI)
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Local Authentication Development (Keycloak)
AegisOne uses Keycloak for local OIDC authentication and identity management.

- **Keycloak Container:** `quay.io/keycloak/keycloak:24.0.1`
- **Local URL:** `http://localhost:8080`
- **Admin Console:** `http://localhost:8080/admin`
- **Documentation:** See [`docs/keycloak-local-development.md`](file:///y:/hemanth%20projects%201/bava/docs/keycloak-local-development.md) for full configuration details.

### 4. Running Tests
```bash
# Run backend tests (132 passed)
cd backend
pytest

# Run frontend tests (16 passed)
cd frontend
npx vitest run
```
