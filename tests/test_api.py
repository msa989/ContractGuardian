from fastapi.testclient import TestClient
from index import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_analyze_rejects_short_text_before_calling_ai():
    response = client.post("/api/analyze", json={"contract_text": "too short"})
    assert response.status_code == 422

def test_analyze_rejects_missing_text():
    response = client.post("/api/analyze", json={})
    assert response.status_code == 422

def test_unknown_route_is_not_found():
    response = client.get("/api/not-a-real-route")
    assert response.status_code == 404
