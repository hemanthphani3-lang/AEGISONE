# AEGISONE — SETUP & RUNTIME GUIDE

## 1. Quick Start with Docker
To spin up the entire AegisOne stack (Keycloak, PostgreSQL, FastAPI Backend, React Frontend):

```bash
docker-compose up --build -d
```

Services will be exposed on:
- **Frontend Portal**: `http://localhost:5173`
- **FastAPI Backend**: `http://localhost:8000`
- **Keycloak Console**: `http://localhost:8080` (Realm: `accessguard`)
- **PostgreSQL**: `localhost:5432`

## 2. Manual Development Setup

### Backend Setup:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

## 3. Running Test Suites
- **Backend Tests**: `pytest` inside `backend/`
- **Frontend Typecheck & Build**: `npm run build` inside `frontend/`
