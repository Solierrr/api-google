import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from opentelemetry import trace
from starlette.exceptions import HTTPException

from app.infrastructure.observability.observability import TRACE_ID_HEADER, mark_error

_log = logging.getLogger("google_registry.errors")

GENERIC_BY_STATUS = {
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    406: "NOT_ACCEPTABLE",
    409: "CONFLICT",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_FAILED",
    429: "RATE_LIMITED",
    502: "DEPENDENCY_UNAVAILABLE",
    503: "DEPENDENCY_UNAVAILABLE",
    504: "DEPENDENCY_UNAVAILABLE",
}


class ApiError(Exception):
    """Erro de negócio com status HTTP e `errorCode` do catálogo, respondido no formato `ProblemDetail`"""

    def __init__(self, status: int, error_code: str, detail: str, **extra):
        super().__init__(detail)
        self.status = status
        self.error_code = error_code
        self.detail = detail
        self.extra = extra


def problem(
    request: Request, status: int, error_code: str, detail: str, headers: dict[str, str] | None = None, **extra
) -> JSONResponse:
    """Monta a resposta `application/problem+json` do contrato de erro da organização"""
    body = {
        "type": "about:blank",
        "title": error_code,
        "status": status,
        "errorCode": error_code,
        "detail": detail,
        "instance": request.url.path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    span = trace.get_current_span().get_span_context()
    if span.is_valid:
        body["traceId"] = format(span.trace_id, "032x")
        # o 500 sai pelo ServerErrorMiddleware, fora do middleware de X-Trace-Id -> header posto aqui também
        headers = {**(headers or {}), TRACE_ID_HEADER: body["traceId"]}
    body.update(extra)
    return JSONResponse(body, status_code=status, headers=headers, media_type="application/problem+json")


def _field(location: tuple) -> str:
    """Caminho do campo inválido, sem a origem (`body`, `query`, `path`, `header`) quando houver campo"""
    parts = location[1:] or location[:1]
    return ".".join(str(part) for part in parts)


def register_error_handlers(app: FastAPI) -> None:
    """Registra os handlers genéricos: `ApiError`, `HTTPException`, validação e erro inesperado"""

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        mark_error(exc)
        return problem(request, exc.status, exc.error_code, exc.detail, **exc.extra)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        mark_error(exc)
        code = GENERIC_BY_STATUS.get(exc.status_code, "INTERNAL_ERROR")
        return problem(request, exc.status_code, code, str(exc.detail), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        mark_error(exc)
        if any(error.get("type") == "json_invalid" for error in exc.errors()):
            return problem(request, 422, "MALFORMED_REQUEST", "O corpo da requisição não é um JSON válido.")
        errors = [
            {"field": _field(tuple(error.get("loc", ()))), "errorCode": "VALIDATION_FAILED", "detail": error["msg"]}
            for error in exc.errors()
        ]
        return problem(request, 422, "VALIDATION_FAILED", "Erro de validação nos campos da requisição.", errors=errors)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        mark_error(exc)
        _log.error("Falha 500 não tratada em %s %s", request.method, request.url.path, exc_info=exc)
        return problem(request, 500, "INTERNAL_ERROR", "Ocorreu um erro interno inesperado.")
