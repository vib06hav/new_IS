from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_api_imports_correctly():
    assert app is not None


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_id_header_is_returned():
    response = client.get("/readiness", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"


def test_readiness_endpoint_reports_checks():
    response = client.get("/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body["checks"]
    assert "storage" in body["checks"]
    assert "llm_config" in body["checks"]
