from fastapi import APIRouter
from app.db.session import check_database_connection

router = APIRouter()


@router.get("/health")
async def get_health() -> dict[str, str]:
    """Health check endpoint returning API and database status."""
    db_connected = await check_database_connection()
    db_status = "connected" if db_connected else "disconnected"
    return {
        "status": "ok",
        "service": "aegisone-api",
        "version": "0.1.0",
        "database": db_status,
    }
