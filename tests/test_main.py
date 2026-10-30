from app.version import VERSION


def test_health_returns_up_with_version(anonymous_client):
    response = anonymous_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP", "version": VERSION}


def test_ready_is_up_after_startup(anonymous_client):
    response = anonymous_client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_is_down_without_http_clients(anonymous_client):
    clients = anonymous_client.app.state.google_http_clients
    anonymous_client.app.state.google_http_clients = {}
    try:
        response = anonymous_client.get("/ready")
    finally:
        anonymous_client.app.state.google_http_clients = clients

    assert response.status_code == 503
    assert response.json() == {"status": "DOWN"}
