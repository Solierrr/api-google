"""
Registra as métricas de chamadas às APIs Google e aos serviços internos Solier

Métricas de domínio (`google.*`, `solier.internal.*`) -> o histograma HTTP do modelo não cobre chamadas de saída
| o meter vem do provider global instalado por setup_observability, sem provider próprio
"""

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram

from app.infrastructure.observability import SERVICE_NAME

# criados no import -> o proxy da API OTel religa os instrumentos quando setup_observability instala o provider
_meter = metrics.get_meter(SERVICE_NAME)

_requests: Counter = _meter.create_counter(
    "google.requests",
    unit="{request}",
    description="Total de requests para APIs Google, por capability e resultado",
)
_request_duration: Histogram = _meter.create_histogram(
    "google.request.duration",
    unit="s",
    description="Duração das requests par APIs Google, por capability e resultado.",
)
_internal_requests: Counter = _meter.create_counter(
    "solier.internal.requests",
    unit="{request}",
    description="Total de requests para serviços internos Solier (api-auth), por serviço e resultado",
)
_internal_request_duration: Histogram = _meter.create_histogram(
    "solier.internal.request.duration",
    unit="s",
    description="Duração das requests para serviços internos Solier, por serviço e resultado.",
)


def record_google_request(
    *, capability: str, duration_seconds: float, status_code: int | None, error_type: str | None
) -> None:
    """Registra uma chamada Google concluída nas duas métricas

    Args:
        capability: nome da capability que originou a chamada
        duration_seconds: tempo total da chamada, incluindo retries
        status_code: status HTTP da resposta (ausente em timeout/erro de rede)
        error_type: valor de `error.type` se a chamada falhou, ou `None` se teve sucesso
    """
    attributes: dict[str, str] = {"google.capability": capability}
    if status_code is not None:
        attributes["http.response.status_code"] = str(status_code)
    if error_type is not None:
        attributes["error.type"] = error_type

    _requests.add(1, attributes)
    _request_duration.record(duration_seconds, attributes)


def record_internal_request(
    *, service: str, duration_seconds: float, status_code: int | None, error_type: str | None
) -> None:
    """Registra uma chamada a um serviço interno Solier concluída nas duas métricas

    Args:
        service: nome do serviço interno chamado
        duration_seconds: tempo total da chamada, incluindo retries
        status_code: status HTTP da resposta (ausente em timeout/erro de rede)
        error_type: valor de `error.type` se a chamada falhou, ou `None` se teve sucesso
    """
    attributes: dict[str, str] = {"solier.service": service}
    if status_code is not None:
        attributes["http.response.status_code"] = str(status_code)
    if error_type is not None:
        attributes["error.type"] = error_type

    _internal_requests.add(1, attributes)
    _internal_request_duration.record(duration_seconds, attributes)
