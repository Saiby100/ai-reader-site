from __future__ import annotations

from fastapi.testclient import TestClient

AUTH_HEADER = {"Authorization": "Bearer test-secret"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_parse_requires_auth(client: TestClient) -> None:
    response = client.post("/parse")
    assert response.status_code == 422


def test_parse_rejects_bad_auth(client: TestClient) -> None:
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer wrong"},
        files={"file": ("test.pdf", b"fake", "application/pdf")},
    )
    assert response.status_code == 401


def test_parse_rejects_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/parse",
        headers=AUTH_HEADER,
        files={"file": ("test.exe", b"fake", "application/octet-stream")},
    )
    assert response.status_code == 415
