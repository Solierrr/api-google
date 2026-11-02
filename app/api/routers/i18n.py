from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_http_client
from app.api.responses import error_responses
from app.application.i18n.service import TranslationService
from app.config import get_settings
from app.infrastructure.auth.service_key import require_caller
from app.infrastructure.google.translation.adapter import TranslationAdapter
from app.infrastructure.http.google_http_client import GoogleHttpClient
from app.schemas.i18n import TranslateRequest, TranslateResponse

router = APIRouter(tags=["Tradução"])


def _get_service(
    http_client: Annotated[GoogleHttpClient, Depends(get_http_client("translation"))],
) -> TranslationService:
    """Monta o `TranslationService` a partir do cliente Google"""
    adapter = TranslationAdapter(http_client, api_key=get_settings().google_key_translation)
    return TranslationService(adapter)


@router.post(
    "/internal/i18n/translate",
    summary="Detecta o idioma de origem e traduz campos de texto pros demais idiomas suportados",
    description="Chamado só pelo api-core, com a chave de serviço dele. O resultado é apenas devolvido.",
    operation_id="translateFields",
    dependencies=[Depends(require_caller("api-core"))],
    responses=error_responses(401, 403, 422, 502, 503, 504),
)
@router.post("/v1/i18n/translate", include_in_schema=False, deprecated=True)
async def translate(
    request: TranslateRequest,
    service: Annotated[TranslationService, Depends(_get_service)],
) -> TranslateResponse:
    """Detecta o idioma de origem dos campos informados e traduz pros demais idiomas suportados (en/es/pt).

    O resultado é apenas devolvido: quem chamou grava onde precisar.
    `/v1/i18n/translate` fica só até o api-core passar a chamar `/internal/i18n/translate`.

    Args:
        request: campos de texto e idioma de origem (opcional)
        service: service com client google injetado

    Returns:
        O idioma de origem detectado e os campos traduzidos

    Raises:
        GoogleUpstreamException: resposta HTTP 200 do Google em formato inesperado
    """
    return await service.translate_fields(request.fields, request.source_language)
