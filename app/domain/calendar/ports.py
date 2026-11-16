from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.schemas.calendar import Event, EventCreate, EventList, EventUpdate, Interval


class RefreshTokenRejected(Exception):
    pass


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)


class CalendarApiPort(Protocol):
    async def free_busy(self, access_token: str, start: datetime, end: datetime) -> list[Interval]: ...

    async def create_event(self, access_token: str, event: EventCreate) -> Event: ...

    async def list_events(
        self, access_token: str, start: datetime, end: datetime, page_token: str | None
    ) -> EventList: ...

    async def update_event(self, access_token: str, event_id: str, update: EventUpdate) -> Event: ...

    async def delete_event(self, access_token: str, event_id: str) -> None: ...


class CalendarOAuthPort(Protocol):
    def authorization_url(self, state: str) -> str: ...

    async def exchange_code(self, code: str) -> OAuthTokens: ...

    async def refresh_access_token(self, refresh_token: str) -> str: ...

    async def revoke(self, token: str) -> None: ...
