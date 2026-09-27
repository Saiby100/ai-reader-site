from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_SECRET", "test-secret")


@pytest.fixture()
def client() -> TestClient:
    from app.main import app

    return TestClient(app)
