from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_http_client
from app.api.responses import error_responses
from app.application.solar.service import SolarService
from app.config import get_settings
from app.infrastructure.auth.service_key import require_caller
from app.infrastructure.google.solar.adapter import SolarAdapter
from app.infrastructure.http.google_http_client import GoogleHttpClient
from app.schemas.solar import SolarViability

router = APIRouter(tags=["Energia solar"])


def _get_service(
    http_client: Annotated[GoogleHttpClient, Depends(get_http_client("solar"))],
) -> SolarService:
    """Monta o `SolarService` a partir do cliente HTTP da capability"""
    return SolarService(SolarAdapter(http_client, api_key=get_settings().google_key_maps))


@router.get(
    "/internal/solar/roof-viability",
    summary="Consulta a viabilidade solar do telhado mais próximo",
    description="Chamado só pelo ai-geographic, com a chave de serviço dele. Toda chamada consulta a Solar API.",
    operation_id="getRoofViability",
    dependencies=[Depends(require_caller("ai-geographic"))],
    responses=error_responses(
        401, 403, 404, 422, 502, 503, 504, descriptions={404: "Sem cobertura de dados solares para a coordenada"}
    ),
)
@router.get("/v1/solar/roof-viability", include_in_schema=False, deprecated=True)
async def get_roof_viability(
    latitude: Annotated[float, Query(ge=-90, le=90, description="Latitude do ponto a consultar")],
    longitude: Annotated[float, Query(ge=-180, le=180, description="Longitude do ponto a consultar")],
    service: Annotated[SolarService, Depends(_get_service)],
) -> SolarViability:
    """Consulta a viabilidade solar do telhado mais próximo da coordenada informada.

    Toda chamada consulta a Solar API do Google.
    `/v1/solar/roof-viability` fica só até o ai-geographic passar a chamar `/internal/solar/roof-viability`.

    Args:
        latitude: latitude do ponto a consultar.
        longitude: longitude do ponto a consultar.
        service: service com client google injetado

    Returns:
        A viabilidade solar do telhado encontrado

    Raises:
        GoogleNotFoundException: sem dado de cobertura para a coordenada informada / HTTP 404
    """
    return await service.get_roof_viability(latitude, longitude)
