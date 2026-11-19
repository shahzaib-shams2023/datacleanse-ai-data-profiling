from fastapi.testclient import TestClient
from app.main import app
from app.data.sample_dirty_data import SAMPLE_DIRTY_CSV

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_samples():
    res = client.get("/api/samples")
    assert res.status_code == 200
    assert "sample_csv" in res.json()


def test_profile_api():
    payload = {"csv_or_json": SAMPLE_DIRTY_CSV}
    res = client.post("/api/profile", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["row_count"] == 11
    assert len(data["anomalies"]) >= 3
    assert data["data_health_score"] > 0


def test_clean_api():
    payload = {"csv_or_json": SAMPLE_DIRTY_CSV}
    res = client.post("/api/clean", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["cleaned_health_score"] > data["initial_health_score"]
    assert len(data["operations_applied"]) >= 3
    assert "import pandas as pd" in data["generated_python_code"]

