import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import TypeVar

from app.domain.calendar.ports import CalendarApiPort, CalendarOAuthPort, RefreshTokenRejected
from app.exceptions import (
    CalendarConsentDeniedException,
    CalendarNotConfiguredException,
    CalendarTokenRevokedException,
    GoogleAuthenticationException,
    GoogleNotFoundException,
    GoogleValidationException,
)
from app.infrastructure.calendar.state import CalendarStateSigner, InvalidStateError
from app.infrastructure.solier.auth.calendar_token_client import (
    STATUS_CONNECTED,
    AuthCalendarTokenClient,
    TechnicianTokens,
)
from app.schemas.calendar import (
    Availability,
    ConnectionStatus,
    ConnectResponse,
    Event,
    EventCreate,
    EventList,
    EventUpdate,
    Interval,
)

_log = logging.getLogger("google_registry.calendar")
_MAX_PERIOD = timedelta(days=60)
_CONSENT_DENIED = "access_denied"
_UNAUTHORIZED = 401
T = TypeVar("T")


class InvalidPeriodError(ValueError):
    pass


class CalendarService:
    def __init__(
        self,
        api: CalendarApiPort,
        oauth: CalendarOAuthPort | None,
        tokens: AuthCalendarTokenClient,
        signer: CalendarStateSigner | None,
    ) -> None:
        self._api = api
        self._oauth = oauth
        self._tokens = tokens
        self._signer = signer

    def connect(self, technician_id: str) -> ConnectResponse:
        oauth, signer = (self._require_oauth(), self._require_signer())
        return ConnectResponse(authorization_url=oauth.authorization_url(signer.sign(technician_id)))

    async def complete_connection(self, code: str | None, state: str, error: str | None) -> ConnectionStatus:
        oauth, signer = (self._require_oauth(), self._require_signer())
        try:
            technician_id = signer.verify(state)
        except InvalidStateError as exc:
            raise GoogleValidationException(
                "state inválido ou expirado", capability="calendar", reason="invalid_state"
            ) from exc
        if error is not None:
            if error == _CONSENT_DENIED:
                raise CalendarConsentDeniedException(
                    "O técnico não autorizou o acesso ao Calendar", technician_id=technician_id
                )
            raise GoogleValidationException(
                "O Google devolveu erro no consentimento", capability="calendar", reason=error
            )
        if not code:
            raise GoogleValidationException("Callback sem code", capability="calendar", reason="missing_code")
        tokens = await oauth.exchange_code(code)
        await self._tokens.save(technician_id, access_token=tokens.access_token, refresh_token=tokens.refresh_token)
        return ConnectionStatus(status="connected")

    async def disconnect(self, technician_id: str) -> None:
        tokens = await self._tokens.get(technician_id)
        if tokens is not None and self._oauth is not None:
            await self._oauth.revoke(tokens.refresh_token)
        await self._tokens.disconnect(technician_id)

    async def get_availability(self, technician_id: str, start: datetime, end: datetime) -> Availability:
        _validate_period(start, end)
        busy = await self._call(technician_id, lambda token: self._api.free_busy(token, start, end))
        return Availability(busy=busy, free=_free_windows(busy, start, end))

    async def create_event(self, technician_id: str, event: EventCreate) -> Event:
        return await self._call(technician_id, lambda token: self._api.create_event(token, event))

    async def list_events(
        self, technician_id: str, start: datetime, end: datetime, page_token: str | None
    ) -> EventList:
        _validate_period(start, end)
        return await self._call(technician_id, lambda token: self._api.list_events(token, start, end, page_token))

    async def update_event(self, technician_id: str, event_id: str, update: EventUpdate) -> Event:
        return await self._call(technician_id, lambda token: self._api.update_event(token, event_id, update))

    async def delete_event(self, technician_id: str, event_id: str) -> None:
        await self._call(technician_id, lambda token: self._api.delete_event(token, event_id))

    async def _call(self, technician_id: str, operation: Callable[[str], Awaitable[T]]) -> T:
        tokens = await self._tokens.get(technician_id)
        if tokens is None or tokens.status != STATUS_CONNECTED:
            raise GoogleNotFoundException("Técnico não conectado ao Google Calendar", capability="calendar")
        try:
            return await operation(tokens.access_token)
        except GoogleAuthenticationException as exc:
            if exc.status_code != _UNAUTHORIZED:
                raise
        access_token = await self._renew_access_token(technician_id, tokens)
        return await operation(access_token)

    async def _renew_access_token(self, technician_id: str, tokens: TechnicianTokens) -> str:
        oauth = self._require_oauth()
        try:
            access_token = await oauth.refresh_access_token(tokens.refresh_token)
        except RefreshTokenRejected as exc:
            await self._tokens.mark_revoked(technician_id)
            raise CalendarTokenRevokedException(
                "O técnico revogou o acesso ao Google Calendar", technician_id=technician_id
            ) from exc
        await self._tokens.save(technician_id, access_token=access_token, refresh_token=tokens.refresh_token)
        return access_token

    def _require_oauth(self) -> CalendarOAuthPort:
        if self._oauth is None:
            raise CalendarNotConfiguredException(
                "OAuth do Google Calendar não configurado neste ambiente", capability="calendar"
            )
        return self._oauth

    def _require_signer(self) -> CalendarStateSigner:
        if self._signer is None:
            raise CalendarNotConfiguredException(
                "CALENDAR_STATE_SECRET não configurado neste ambiente", capability="calendar"
            )
        return self._signer


def _validate_period(start: datetime, end: datetime) -> None:
    if start >= end:
        raise InvalidPeriodError("from precisa ser anterior a to")
    if end - start > _MAX_PERIOD:
        raise InvalidPeriodError("o período máximo é de 60 dias")


def _free_windows(busy: list[Interval], start: datetime, end: datetime) -> list[Interval]:
    merged: list[tuple[datetime, datetime]] = []
    for interval in sorted(busy, key=lambda item: item.start):
        busy_start, busy_end = (max(interval.start, start), min(interval.end, end))
        if busy_start >= busy_end:
            continue
        if merged and busy_start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], busy_end))
        else:
            merged.append((busy_start, busy_end))
    free: list[Interval] = []
    cursor = start
    for busy_start, busy_end in merged:
        if busy_start > cursor:
            free.append(Interval(start=cursor, end=busy_start))
        cursor = busy_end
    if cursor < end:
        free.append(Interval(start=cursor, end=end))
    return free
