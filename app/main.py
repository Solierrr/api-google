from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import address, geo, health, i18n, solar
from app.config import WebSettings, get_settings
from app.exceptions.handlers import register_exception_handlers
from app.infrastructure.http.google_http_client import GoogleHttpClient
from app.infrastructure.http.internal_http_client import InternalHttpClient
from app.infrastructure.observability import SERVICE_NAME
from app.infrastructure.observability.observability import setup_observability
from app.infrastructure.observability.redaction import (
    async_redact_url_in_span,
    redact_url_in_span,
    silence_url_loggers,
)
from app.openapi import install_openapi
from app.version import VERSION

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


_web = WebSettings()

app = FastAPI(
    title="Solaria — api-google",
    description=(
        "Ponto único de acesso às APIs do Google da Solaria: endereços (Places, Geocoding e Address Validation), "
        "fuso horário, viabilidade solar e tradução. Sem estado: só consulta o Google e devolve o resultado. "
        "Pessoas autenticam com o JWT do api-auth (bearerAuth); serviços chamam as rotas /internal com a chave "
        "de serviço (serviceKey)."
    ),
    version=VERSION,
    contact={"name": "Solaria", "url": "https://github.com/Solierrr"},
    license_info={"name": "CC0-1.0", "url": "https://creativecommons.org/publicdomain/zero/1.0/"},
    servers=[
        {"url": "https://google-registry.onrender.com", "description": "QA"},
        {"url": "http://localhost:8000", "description": "Local"},
    ],
    openapi_tags=[
        {"name": "Endereços", "description": "Sugestão, detalhe, geocodificação, validação e resolução de endereços"},
        {"name": "Energia solar", "description": "Viabilidade solar de telhados pela Solar API"},
        {"name": "Geografia", "description": "Fuso horário de coordenadas, calculado sem API externa"},
        {"name": "Saúde", "description": "Rotas de vivo e pronto da plataforma"},
        {"name": "Tradução", "description": "Detecção de idioma e tradução de campos de texto"},
    ],
    docs_url="/docs" if _web.docs_enabled else None,
    openapi_url="/openapi.json" if _web.docs_enabled else None,
    redoc_url=None,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
        "tagsSorter": "alpha",
        "operationsSorter": "alpha",
    },
    lifespan=_lifespan,
)

# logo após criar a app, nesta ordem -> erros usam o span criado pela observabilidade
setup_observability(
    app,
    SERVICE_NAME,
    request_hook=redact_url_in_span,
    async_request_hook=async_redact_url_in_span,
)
silence_url_loggers()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_web.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_openapi(app)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(address.router)
app.include_router(solar.router)
app.include_router(geo.router)
app.include_router(i18n.router)
