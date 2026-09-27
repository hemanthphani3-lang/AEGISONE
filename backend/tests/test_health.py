from fastapi.testclient import TestClient
from app.main import app


def test_import_app():
    """Verify that the FastAPI application can be imported successfully."""
    assert app is not None


def test_health_check():
    """Test the GET /api/v1/health endpoint."""
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "aegisone-api"
    assert data["version"] == "0.1.0"


def test_invalid_route():
    """Verify that an invalid endpoint returns HTTP 404."""
    client = TestClient(app)
    response = client.get("/api/v1/nonexistent")

    assert response.status_code == 404
