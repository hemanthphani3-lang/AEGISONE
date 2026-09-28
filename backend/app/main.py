from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.evaluate import router as evaluate_router
from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.intelligence import router as intelligence_router
from app.api.policies import router as policies_router
from app.api.simulate import router as simulate_router
from app.mfa import mfa_router
from app.users import users_router
from app.config import settings
from app.core.correlation import CorrelationMiddleware
from app.db.session import check_database_connection, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager that autoruns database schema creation on startup."""
    if await check_database_connection():
        try:
            await create_tables()
            print("[INFO] Database schema verified and tables created successfully.")
        except Exception as err:
            print(f"[WARNING] Automatic schema creation warning: {err}")
    yield


app = FastAPI(
    title="AegisOne API",
    version="0.1.0",
    description="Zero-cost Conditional Access Policy Lab / Simulator",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)

# Configure CORS using environment-configured origins and Vercel preview origin regex
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.allowed_origins,
    allow_origin_regex=r"https://aegisone-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint returning API service status and endpoint discovery."""
    return {
        "name": "AegisOne API",
        "version": "0.1.0",
        "status": "online",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/v1/health",
    }


# Primary API v1 route prefixing
app.include_router(health_router, prefix="/api/v1")
app.include_router(policies_router, prefix="/api/v1")
app.include_router(evaluate_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(simulate_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(mfa_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

# Top-level route aliases (enables direct /health, /auth/me, /policies/intelligence, etc.)
app.include_router(health_router)
app.include_router(policies_router)
app.include_router(evaluate_router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(simulate_router)
app.include_router(intelligence_router)
app.include_router(incidents_router)
app.include_router(mfa_router)
app.include_router(users_router)


