# Local Keycloak Authentication Setup Guide for AegisOne

This document outlines the local development setup for Keycloak authentication in **AegisOne**.

---

## 1. Prerequisites

- **Docker Desktop** (version 20+ with Docker Compose v2/v5)
- Docker Desktop background service (`com.docker.service`) must be running.

---

## 2. Keycloak Architecture & Container Details

- **Official Docker Image:** `quay.io/keycloak/keycloak:24.0.1`
- **Execution Mode:** Development mode (`start-dev --import-realm`)
- **Local Endpoint:** `http://localhost:8080`
- **Administration Console:** `http://localhost:8080/admin`
- **Pre-configured Realm File:** `./keycloak/accessguard-realm.json`

---

## 3. How to Start, Stop, and Restart Keycloak

### Start Keycloak Service
```bash
docker compose up -d keycloak
```

### Check Container Status
```bash
docker ps
```

### View Keycloak Container Logs
```bash
docker logs accessguard-keycloak -f
```

### Stop Keycloak Service
```bash
docker compose stop keycloak
```

### Restart Keycloak Service
```bash
docker compose restart keycloak
```

---

## 4. Environment Variables

### Backend (`backend/.env`)
```ini
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=accessguard
KEYCLOAK_CLIENT_ID=accessguard-backend
KEYCLOAK_CLIENT_SECRET=accessguard-secret-dev
```

### Frontend (`frontend/.env`)
```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=accessguard
VITE_KEYCLOAK_CLIENT_ID=accessguard-backend
```

*Note: Never include client secrets or database passwords in frontend `.env` files.*

---

## 5. Troubleshooting & Health Checks

- **Health Endpoint:** `http://localhost:8080/health/ready`
- **Port Conflict (Port 8080 in use):**
  If port `8080` is occupied by another local service, update the host port binding in `docker-compose.yml` (e.g., `"8081:8080"`) and align `KEYCLOAK_URL` in `.env` accordingly.
- **Docker Daemon Connection Errors:**
  Ensure Docker Desktop is launched and the Linux engine pipe (`//./pipe/dockerDesktopLinuxEngine`) is active.
