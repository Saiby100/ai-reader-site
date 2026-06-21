import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_SECRET", "test-secret")


@pytest.fixture()
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


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


# --- pure helpers (no model loading) ---


class _Enum:
    def __init__(self, value: str) -> None:
        self.value = value


class _Prov:
    def __init__(self, page_no: int, charspan: tuple[int, int]) -> None:
        self.page_no = page_no
        self.charspan = charspan


class _Item:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


def test_enum_value_handles_enums_strings_and_none() -> None:
    from app.parser import _enum_value

    assert _enum_value(_Enum("success")) == "success"
    assert _enum_value("good") == "good"
    assert _enum_value(None) is None


def test_code_language_drops_unknown() -> None:
    from app.parser import _code_language

    assert _code_language(_Item(code_language=_Enum("Python"))) == "Python"
    assert _code_language(_Item(code_language=_Enum("unknown"))) is None
    assert _code_language(_Item()) is None


def test_element_meta_extracts_ref_page_label_charspan() -> None:
    from app.parser import _element_meta

    item = _Item(
        self_ref="#/texts/12",
        label=_Enum("text"),
        prov=[_Prov(page_no=3, charspan=(18, 24))],
    )
    meta = _element_meta(item)
    assert meta == {
        "ref": "#/texts/12",
        "page": 3,
        "label": "text",
        "charspan": (18, 24),
    }


def test_element_meta_tolerates_missing_provenance() -> None:
    from app.parser import _element_meta

    meta = _element_meta(_Item(self_ref="#/texts/1"))
    assert meta == {"ref": "#/texts/1", "page": None, "label": None, "charspan": None}
