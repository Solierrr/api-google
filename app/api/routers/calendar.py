from datetime import datetime
from typing import Annotated, cast
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_calendar_token_client, get_http_client
from app.application.calendar.service import CalendarService, InvalidPeriodError
from app.config import get_settings
from app.exceptions import CalendarConsentDeniedException
from app.infrastructure.auth.bearer_auth import require_authenticated_user
from app.infrastructure.calendar.state import CalendarStateSigner
from app.infrastructure.google.calendar.adapter import CalendarAdapter
from app.infrastructure.google.calendar.oauth_adapter import CalendarOAuthAdapter, OAuthClientConfig
from app.infrastructure.http.google_http_client import GoogleHttpClient
from app.infrastructure.solier.auth.calendar_token_client import AuthCalendarTokenClient
from app.schemas.calendar import ConnectResponse, Event, EventCreate, EventList

router = APIRouter(prefix="/v1/calendar/me", tags=["Calendar"])
public_router = APIRouter(prefix="/v1/calendar", tags=["Calendar"])
Actor = Annotated[str, Depends(require_authenticated_user)]


class CalendarConnection(BaseModel):
    configured: bool
    connected: bool = False
    reconnect_required: bool = False


class ActivityExport(EventCreate):
    source_id: str = Field(min_length=1, max_length=200)


def configured() -> bool:
    settings = get_settings()
    return all(
        (
            settings.google_calendar_oauth_client_id,
            settings.google_calendar_oauth_client_secret,
            settings.google_calendar_oauth_redirect_uri,
            settings.calendar_state_secret,
            settings.service_key_google_registry,
        )
    )


def calendar_service(
    api: Annotated[GoogleHttpClient, Depends(get_http_client("calendar"))],
    oauth: Annotated[GoogleHttpClient, Depends(get_http_client("calendar_oauth"))],
    tokens: Annotated[AuthCalendarTokenClient, Depends(get_calendar_token_client)],
) -> CalendarService:
    settings = get_settings()
    adapter = None
    signer = None
    if configured():
        adapter = CalendarOAuthAdapter(
            oauth,
            OAuthClientConfig(
                cast(str, settings.google_calendar_oauth_client_id),
                cast(str, settings.google_calendar_oauth_client_secret),
                cast(str, settings.google_calendar_oauth_redirect_uri),
            ),
        )
        signer = CalendarStateSigner(cast(str, settings.calendar_state_secret))
    return CalendarService(CalendarAdapter(api), adapter, tokens, signer)


Service = Annotated[CalendarService, Depends(calendar_service)]


@router.get("/connection", operation_id="getOwnCalendarConnection", response_model=CalendarConnection)
async def connection(actor: Actor, tokens: Annotated[AuthCalendarTokenClient, Depends(get_calendar_token_client)]):
    if not configured():
        return CalendarConnection(configured=False)
    saved = await tokens.get(actor)
    return CalendarConnection(
        configured=True,
        connected=saved is not None and saved.status == "CONNECTED",
        reconnect_required=saved is not None and saved.status == "REVOKED",
    )


@router.post("/connection", operation_id="connectOwnCalendar", response_model=ConnectResponse)
async def connect(actor: Actor, service: Service):
    return service.connect(actor)


@router.delete("/connection", operation_id="disconnectOwnCalendar", status_code=204)
async def disconnect(actor: Actor, service: Service):
    await service.disconnect(actor)
    return Response(status_code=204)


@router.get("/events", operation_id="listOwnCalendarEvents", response_model=EventList)
async def events(
    actor: Actor,
    service: Service,
    start: Annotated[datetime, Query(alias="from")],
    end: Annotated[datetime, Query(alias="to")],
    page_token: str | None = None,
):
    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(422, "O período precisa incluir o fuso horário")
    try:
        return await service.list_events(actor, start, end, page_token)
    except InvalidPeriodError as error:
        raise HTTPException(422, str(error)) from error


@router.post("/events", operation_id="exportOwnCalendarActivity", response_model=Event)
async def export(actor: Actor, event: ActivityExport, service: Service):
    return await service.create_event(actor, event.model_copy(update={"source_id": f"{actor}/{event.source_id}"}))


@public_router.get(
    "/callback",
    operation_id="completeCalendarAuthorization",
    response_class=HTMLResponse,
    openapi_extra={"security": []},
)
async def callback(service: Service, state: str, code: str | None = None, error: str | None = None):
    target = get_settings().calendar_mobile_return_uri
    if target not in ("solaria-qa://calendar/callback", "solaria://calendar/callback") or urlsplit(target).query:
        raise HTTPException(503, "Retorno do app não configurado")
    title = "Google Agenda conectado"
    message = "Você pode voltar ao aplicativo. Suas atividades do Solaria continuam independentes."
    try:
        await service.complete_connection(code, state, error)
    except CalendarConsentDeniedException:
        title = "Permissão não concedida"
        message = "Sua agenda do Solaria continua disponível. Você pode conectar o Google novamente pelo aplicativo."
    return HTMLResponse(
        '<!doctype html><html lang="pt-BR"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title><body><main><h1>{title}</h1><p>{message}</p>"
        f'<a href="{target}">Voltar ao aplicativo</a></main></body></html>',
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        },
    )
