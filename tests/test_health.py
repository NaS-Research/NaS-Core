from fastapi.testclient import TestClient

from nas_core.api.main import app
from nas_core.api.routes.health import require_database


def test_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_readiness_when_database_is_available() -> None:
    app.dependency_overrides[require_database] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "version": "0.1.0"}
