from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health/ready")
    assert r.status_code == 200

def test_now():
    r = client.get("/api/now")
    assert r.status_code == 200
    assert "planets" in r.json()
