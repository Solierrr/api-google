from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routers import address, geo, i18n, solar
from app.config import get_settings
from app.infrastructure.http.google_http_client import GoogleHttpClient
from app.infrastructure.http.internal_http_client import InternalHttpClient
from app.infrastructure.observability import SERVICE_NAME
from app.infrastructure.observability.errors import register_error_handlers
from app.infrastructure.observability.observability import setup_observability
from app.infrastructure.observability.redaction import (
    async_redact_url_in_span,
    redact_url_in_span,
    silence_url_loggers,
)

# Base URL por capability Google - chave usada em app.api.dependencies.get_http_client(capability)
_GOOGLE_BASE_URLS = {
    "address_validation": "https://addressvalidation.googleapis.com",
    "geocoding": "https://maps.googleapis.com",
    "places": "https://places.googleapis.com",
    "solar": "https://solar.googleapis.com",
    "translation": "https://translation.googleapis.com",
}


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    app.state.google_http_clients = {
        capability: GoogleHttpClient(base_url=base_url, capability=capability)
        for capability, base_url in _GOOGLE_BASE_URLS.items()
    }
    app.state.internal_http_clients = {
        "auth": InternalHttpClient(base_url=settings.auth_base_url, service="auth"),
    }

    yield

    for client in app.state.google_http_clients.values():
        await client.aclose()
    for client in app.state.internal_http_clients.values():
        await client.aclose()


app = FastAPI(title="google-registry", lifespan=_lifespan)

# logo após criar a app, nesta ordem -> erros usam o span criado pela observabilidade
setup_observability(
    app,
    SERVICE_NAME,
    request_hook=redact_url_in_span,
    async_request_hook=async_redact_url_in_span,
)
silence_url_loggers()
register_error_handlers(app)

app.include_router(address.router)
app.include_router(solar.router)
app.include_router(geo.router)
app.include_router(i18n.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Healthcheck simples, sem dependências externas"""
    return {"status": "ok"}
