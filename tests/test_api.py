import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

def test_pdf_rejects_invalid_pdf_bytes():
    response = client.post(
        "/api/analyze-pdf",
        files={"file": ("broken.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400


def test_valid_request_reports_missing_server_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/api/analyze",
        json={"contract_text": "This agreement requires written notice at least 180 days before the end of the lease term."},
    )
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]
