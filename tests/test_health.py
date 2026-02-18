from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_ok():
    """GET /health returns a basic status payload."""

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data

