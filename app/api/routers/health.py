from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.version import VERSION

router = APIRouter(tags=["Saúde"])


class HealthResponse(BaseModel):
    """Estado do processo"""

    status: str = Field(..., description="UP quando o processo responde", examples=["UP"])
    version: str = Field(..., description="Versão do release em execução", examples=["0.3.0"])


class ReadyResponse(BaseModel):
    """Prontidão do serviço"""

    status: str = Field(..., description="UP quando o serviço pode atender, DOWN quando não", examples=["UP"])


@router.get(
    "/health",
    summary="Indica se o processo está vivo",
    operation_id="getHealth",
    openapi_extra={"security": []},
)
async def health() -> HealthResponse:
    """Responde sem consultar nenhuma dependência"""
    return HealthResponse(status="UP", version=VERSION)


@router.get(
    "/ready",
    summary="Indica se o serviço está pronto para atender",
    description=(
        "O serviço não guarda estado: fica pronto quando os clientes HTTP do Google e do api-auth foram criados. "
        'Quando não está pronto, responde 503 com {"status": "DOWN"}.'
    ),
    operation_id="getReady",
    openapi_extra={"security": []},
    response_model=ReadyResponse,
)
async def ready(request: Request) -> JSONResponse:
    """Confere se o lifespan já criou os clientes HTTP, sem chamar o Google (cada chamada gasta quota)"""
    state = request.app.state
    if getattr(state, "google_http_clients", None) and getattr(state, "internal_http_clients", None):
        return JSONResponse({"status": "UP"})
    return JSONResponse({"status": "DOWN"}, status_code=503)
