import logging
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.dependencies import get_calendar_token_client
from app.api.routers.calendar import calendar_service
from app.infrastructure.observability.logging import CalendarCallbackFilter
from app.main import app
from app.schemas.calendar import ConnectResponse, Event, EventList


@pytest.fixture
def service():
    fake = Mock()
    fake.connect.return_value = ConnectResponse(authorization_url="https://accounts.google.com/authorize")
    fake.list_events = AsyncMock(return_value=EventList(events=[]))
    fake.create_event = AsyncMock(return_value=Event(event_id="exported"))
    fake.complete_connection = AsyncMock()
    app.dependency_overrides[calendar_service] = lambda: fake
    yield fake
    app.dependency_overrides.pop(calendar_service, None)


def test_requires_authenticated_user(anonymous_client, service):
    assert anonymous_client.post("/v1/calendar/me/connection").status_code == 401
    service.connect.assert_not_called()


def test_connect_is_owned_by_jwt_subject(client, service):
    assert client.post("/v1/calendar/me/connection?technician_id=other-user").status_code == 200
    service.connect.assert_called_once_with("user-1")


def test_export_namespaces_source_and_never_accepts_another_actor(client, service):
    body = {
        "source_id": "project/activity",
        "title": "Visita",
        "start": "2030-01-02T10:00:00Z",
        "end": "2030-01-02T11:00:00Z",
        "technician_id": "other",
    }
    assert client.post("/v1/calendar/me/events", json=body).status_code == 200
    actor, event = service.create_event.call_args.args
    assert actor == "user-1"
    assert event.source_id == "user-1/project/activity"
    body["end"] = body["start"]
    assert client.post("/v1/calendar/me/events", json=body).status_code == 422


def test_period_must_be_aware_and_at_most_sixty_days(client, service):
    assert (
        client.get(
            "/v1/calendar/me/events", params={"from": "2030-01-01T00:00:00", "to": "2030-01-02T00:00:00"}
        ).status_code
        == 422
    )
    service.list_events.assert_not_called()


def test_callback_contains_only_fixed_return_uri(anonymous_client, service):
    response = anonymous_client.get("/v1/calendar/callback", params={"state": "signed", "code": "private-code"})
    assert response.status_code == 200
    assert "solaria-qa://calendar/callback" in response.text
    assert "private-code" not in response.text
    assert response.headers["cache-control"] == "no-store"
    service.complete_connection.assert_awaited_once_with("private-code", "signed", None)


def test_unconfigured_status_does_not_read_tokens(client, monkeypatch):
    monkeypatch.delenv("CALENDAR_STATE_SECRET", raising=False)
    fake = Mock(get=AsyncMock())
    app.dependency_overrides[get_calendar_token_client] = lambda: fake
    try:
        assert client.get("/v1/calendar/me/connection").json() == {
            "configured": False,
            "connected": False,
            "reconnect_required": False,
        }
        fake.get.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_calendar_token_client, None)


def test_callback_access_log_redacts_oauth_values():
    record = logging.LogRecord(
        "uvicorn.access",
        20,
        "",
        0,
        "%s %s %s %s %s",
        ("client", "GET", "/v1/calendar/callback?code=private&state=signed", "1.1", 200),
        None,
    )
    CalendarCallbackFilter().filter(record)
    assert "private" not in record.getMessage()
    assert "signed" not in record.getMessage()


def test_denied_consent_returns_safe_page_without_oauth_query(anonymous_client, service):
    from app.exceptions import CalendarConsentDeniedException
    service.complete_connection.side_effect = CalendarConsentDeniedException("denied", technician_id="user-1")
    response = anonymous_client.get("/v1/calendar/callback", params={"state": "signed", "error": "access_denied"})
    assert response.status_code == 200
    assert "Permissão não concedida" in response.text
    assert "Google Agenda conectado</h1>" not in response.text
    assert "signed" not in response.text
