import logging
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from app.domain.calendar.ports import CalendarOAuthPort, OAuthTokens, RefreshTokenRejected
from app.exceptions import GoogleProviderException, GoogleUpstreamException, GoogleValidationException
from app.infrastructure.http.google_http_client import GoogleHttpClient

_log = logging.getLogger("google_registry.calendar.oauth")
_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_PATH = "/token"
_REVOKE_PATH = "/revoke"
_SCOPES = ("https://www.googleapis.com/auth/calendar.events",)


@dataclass(frozen=True)
class OAuthClientConfig:
    client_id: str
    client_secret: str = field(repr=False)
    redirect_uri: str


class CalendarOAuthAdapter(CalendarOAuthPort):
    def __init__(self, http_client: GoogleHttpClient, config: OAuthClientConfig) -> None:
        self._http_client = http_client
        self._config = config

    def authorization_url(self, state: str) -> str:
        query = urlencode(
            {
                "client_id": self._config.client_id,
                "redirect_uri": self._config.redirect_uri,
                "response_type": "code",
                "scope": " ".join(_SCOPES),
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
        return f"{_AUTHORIZATION_ENDPOINT}?{query}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        response = await self._http_client.request(
            "POST",
            _TOKEN_PATH,
            data={
                "code": code,
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "redirect_uri": self._config.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        payload = _json_object(response)
        access_token, refresh_token = (payload.get("access_token"), payload.get("refresh_token"))
        if not isinstance(access_token, str) or not isinstance(refresh_token, str):
            raise GoogleUpstreamException(
                "Resposta do OAuth do Google sem os tokens esperados", capability="calendar_oauth"
            )
        return OAuthTokens(access_token=access_token, refresh_token=refresh_token)

    async def refresh_access_token(self, refresh_token: str) -> str:
        try:
            response = await self._http_client.request(
                "POST",
                _TOKEN_PATH,
                data={
                    "refresh_token": refresh_token,
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "grant_type": "refresh_token",
                },
                retry=True,
            )
        except GoogleValidationException as exc:
            if exc.reason == "invalid_grant":
                raise RefreshTokenRejected from exc
            raise
        access_token = _json_object(response).get("access_token")
        if not isinstance(access_token, str):
            raise GoogleUpstreamException("Resposta do OAuth do Google sem access_token", capability="calendar_oauth")
        return access_token

    async def revoke(self, token: str) -> None:
        try:
            await self._http_client.request("POST", _REVOKE_PATH, data={"token": token}, retry=True)
        except GoogleProviderException as exc:
            _log.warning("Falha ao revogar o token no Google (%s); seguindo com a desconexão", exc.error_type)


def _json_object(response: Any) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleUpstreamException(
            "Resposta do OAuth do Google em formato inesperado", capability="calendar_oauth"
        ) from exc
    if not isinstance(payload, dict):
        raise GoogleUpstreamException("Resposta do OAuth do Google em formato inesperado", capability="calendar_oauth")
    return payload
