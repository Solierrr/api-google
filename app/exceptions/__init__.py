"""
Exceções de falha nas chamadas a APIs Google e a serviços internos Solier, todas ApiError do modelo de erro

Quem lança escolhe a subclasse e o handler global do modelo monta o ProblemDetail: errorCode = nome da classe em
UPPER_SNAKE sem o sufixo Exception | capability/service e error_type alimentam as métricas
"""

import re
from typing import Any

from app.infrastructure.observability.errors import ApiError


def _error_code(class_name: str) -> str:
    """GoogleAuthenticationException -> GOOGLE_AUTHENTICATION"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name.removesuffix("Exception")).upper()


class GoogleProviderException(ApiError):
    """Converte a falha de uma API Google em ApiError, com a capability de origem

    status = http_status e errorCode = nome da classe -> o cliente recebe o contrato certo só pela subclasse
    | equivale ao BusinessException do api-core
    """

    http_status: int = 502
    #: Valor de `error.type` nas métricas desta exception
    error_type: str = "unknown"

    def __init__(
        self, message: str, *, capability: str, status_code: int | None = None, reason: str | None = None
    ) -> None:
        self.capability = capability
        self.status_code = status_code
        #: Motivo estruturado devolvido pelo Google
        self.reason = reason
        super().__init__(message, self.details())

    @property
    def status(self) -> int:
        """Status HTTP do ProblemDetail (`ApiError.status`)"""
        return self.http_status

    @property
    def error_code(self) -> str:
        """errorCode do ProblemDetail, derivado do nome da classe"""
        return _error_code(type(self).__name__)

    def details(self) -> dict[str, Any] | None:
        """Detalhes estruturados para o payload da exception (`None` = sem detalhes)"""
        return None


class GoogleAuthenticationException(GoogleProviderException):
    """api key google inválida | erro de config"""

    http_status = 502
    error_type = "authentication"


class GoogleAuthorizationException(GoogleProviderException):
    """sem permissão ou consentimento para operação"""

    http_status = 502
    error_type = "authorization"


class GoogleRateLimitException(GoogleProviderException):
    """quota do Google excedida para requests"""

    http_status = 503
    error_type = "rate_limit"


class GoogleValidationException(GoogleProviderException):
    """request rejeitada pelo Google por parâmetro obrigatório ausente ou malformado"""

    http_status = 400
    error_type = "validation"


class GoogleNotFoundException(GoogleProviderException):
    """dado não encontrado pelo Google"""

    http_status = 404
    error_type = "not_found"


class GoogleTimeoutException(GoogleProviderException):
    """chamda pelo google excedeu o timeout configurado no client"""

    http_status = 504
    error_type = "timeout"


class GoogleUnavailableException(GoogleProviderException):
    """falha do lado do Google após as tentativas de retry"""

    http_status = 503
    error_type = "unavailable"


class GoogleUpstreamException(GoogleProviderException):
    """fallback para erro do Google não mapeado -> status HTTP inesperado ou payload HTTP 200 inválido"""

    http_status = 502
    error_type = "upstream"


class CalendarTokenRevokedException(GoogleProviderException):
    """O técnico revogou|não permitiu o consentimento OAuth do Calendar

    Não deve ser tentado novamente sem consentimento do técnico
    """

    http_status = 409
    error_type = "token_revoked"

    def __init__(self, message: str, *, technician_id: str) -> None:
        # antes do super: details() (que vai para o corpo do erro) lê technician_id
        self.technician_id = technician_id
        super().__init__(message, capability="calendar")

    def details(self) -> dict[str, Any]:
        return {"technician_id": self.technician_id}


class InternalServiceException(ApiError):
    """Converte a falha de um serviço interno Solier (api-auth) em ApiError, com o serviço de origem

    status = http_status e errorCode = nome da classe | equivale ao BusinessException do api-core
    """

    http_status: int = 502
    #: Valor de `error.type` nas métricas desta exception
    error_type: str = "unknown"

    def __init__(self, message: str, *, service: str, status_code: int | None = None) -> None:
        self.service = service
        self.status_code = status_code
        super().__init__(message, self.details())

    @property
    def status(self) -> int:
        """Status HTTP do ProblemDetail (`ApiError.status`)"""
        return self.http_status

    @property
    def error_code(self) -> str:
        """errorCode do ProblemDetail, derivado do nome da classe"""
        return _error_code(type(self).__name__)

    def details(self) -> dict[str, Any] | None:
        """Detalhes estruturados para o payload da exception (`None` = sem detalhes)"""
        return None


class InternalServiceValidationException(InternalServiceException):
    """Requisição rejeitada pelo serviço interno por parâmetro obrigatório ausente ou malformado"""

    http_status = 400
    error_type = "validation"


class InternalServiceNotFoundException(InternalServiceException):
    """Recurso não encontrado no serviço interno"""

    http_status = 404
    error_type = "not_found"


class InternalServiceTimeoutException(InternalServiceException):
    """Chamada ao serviço interno excedeu o timeout configurado no client"""

    http_status = 504
    error_type = "timeout"


class InternalServiceUnavailableException(InternalServiceException):
    """Falha do lado do serviço interno (rede ou 5xx) após as tentativas de retry"""

    http_status = 503
    error_type = "unavailable"


class InternalServiceUpstreamException(InternalServiceException):
    """Fallback para erro do serviço interno não mapeado -> status HTTP inesperado (ex.: 401/403/429)"""

    http_status = 502
    error_type = "upstream"
