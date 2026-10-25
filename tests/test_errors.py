import httpx
import respx

GEOCODE = "https://maps.googleapis.com/maps/api/geocode/json"
PROBLEM_FIELDS = {"type", "title", "status", "errorCode", "detail", "instance", "timestamp"}


def test_validation_error_uses_problem_detail(client):
    response = client.get("/v1/geo/timezone", params={"latitude": 91, "longitude": 0})

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert PROBLEM_FIELDS <= body.keys()
    assert body["type"] == "about:blank"
    assert body["errorCode"] == body["title"] == "VALIDATION_FAILED"
    assert body["instance"] == "/v1/geo/timezone"
    assert body["errors"] == [
        {"field": "latitude", "errorCode": "VALIDATION_FAILED", "detail": body["errors"][0]["detail"]}
    ]


def test_malformed_body_returns_malformed_request(client):
    response = client.post("/v1/address/geocode", content=b"{not json", headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert response.json()["errorCode"] == "MALFORMED_REQUEST"


def test_unknown_route_returns_not_found(client):
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["errorCode"] == "NOT_FOUND"


def test_method_not_allowed_uses_generic_code(client):
    response = client.delete("/health")

    assert response.status_code == 405
    assert response.json()["errorCode"] == "METHOD_NOT_ALLOWED"


@respx.mock
def test_google_rejection_returns_upstream_request_rejected(client):
    respx.get(GEOCODE).mock(return_value=httpx.Response(200, json={"status": "INVALID_REQUEST"}))

    response = client.post("/v1/address/geocode", json={"address": "Av. Paulista"})

    assert response.status_code == 400
    body = response.json()
    assert body["errorCode"] == "UPSTREAM_REQUEST_REJECTED"
    assert PROBLEM_FIELDS <= body.keys()
