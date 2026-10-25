import httpx
import pytest
import respx
from pydantic import ValidationError

from app.config import Settings

API_CORE_KEY = "test-service-key-api-core-0000000000"
AI_GEOGRAPHIC_KEY = "test-service-key-ai-geographic-00000"
TRANSLATE = "https://translation.googleapis.com/language/translate/v2"
FIND_CLOSEST = "https://solar.googleapis.com/v1/buildingInsights:findClosest"


def test_user_route_without_token_returns_401(anonymous_client):
    response = anonymous_client.get("/v1/geo/timezone", params={"latitude": -3.1, "longitude": -60.0})

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["errorCode"] == "UNAUTHENTICATED"


def test_address_route_without_token_returns_401(anonymous_client):
    response = anonymous_client.post("/v1/address/geocode", json={"address": "Av. Paulista"})

    assert response.status_code == 401


def test_internal_route_without_key_returns_401(client):
    response = client.post("/internal/i18n/translate", json={"fields": [{"field_name": "title", "text": "Curso"}]})

    assert response.status_code == 401
    body = response.json()
    assert body["errorCode"] == "UNAUTHENTICATED"
    assert body["detail"] == "Chave de serviço ausente ou inválida."


def test_internal_route_with_unknown_key_returns_401(client):
    response = client.post(
        "/internal/i18n/translate",
        json={"fields": [{"field_name": "title", "text": "Curso"}]},
        headers={"X-Service-Key": "x" * 40},
    )

    assert response.status_code == 401


def test_internal_route_rejects_caller_not_accepted(client):
    response = client.post(
        "/internal/i18n/translate",
        json={"fields": [{"field_name": "title", "text": "Curso"}]},
        headers={"X-Service-Key": AI_GEOGRAPHIC_KEY},
    )

    assert response.status_code == 403
    assert response.json()["errorCode"] == "FORBIDDEN"


@respx.mock
def test_api_core_translates_with_its_service_key(client):
    respx.post(f"{TRANSLATE}/detect").mock(
        return_value=httpx.Response(200, json={"data": {"detections": [[{"language": "pt"}]]}})
    )
    respx.post(TRANSLATE).mock(
        return_value=httpx.Response(200, json={"data": {"translations": [{"translatedText": "Translated"}]}})
    )

    response = client.post(
        "/internal/i18n/translate",
        json={"fields": [{"field_name": "title", "text": "Curso"}]},
        headers={"X-Service-Key": API_CORE_KEY},
    )

    assert response.status_code == 200
    assert response.json()["source_language"] == "pt"


@respx.mock
def test_ai_geographic_reads_roof_viability_with_its_service_key(client):
    respx.get(FIND_CLOSEST).mock(return_value=httpx.Response(404))

    response = client.get(
        "/internal/solar/roof-viability",
        params={"latitude": -23.5, "longitude": -46.6},
        headers={"X-Service-Key": AI_GEOGRAPHIC_KEY},
    )

    assert response.status_code == 404
    assert response.json()["errorCode"] == "NOT_FOUND"


def test_api_core_cannot_read_roof_viability(client):
    response = client.get(
        "/internal/solar/roof-viability",
        params={"latitude": -23.5, "longitude": -46.6},
        headers={"X-Service-Key": API_CORE_KEY},
    )

    assert response.status_code == 403


def test_short_service_key_prevents_startup(monkeypatch):
    monkeypatch.setenv("SERVICE_KEY_API_CORE", "short")

    with pytest.raises(ValidationError):
        Settings()


def test_empty_service_key_counts_as_absent(monkeypatch):
    monkeypatch.setenv("SERVICE_KEY_API_CORE", "")

    assert Settings().service_keys["api-core"] is None
