from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.schemas.problem import ProblemDetail

_PROBLEM_REF = {"$ref": "#/components/schemas/ProblemDetail"}

_CODES_BY_STATUS = {
    "400": ["UPSTREAM_REQUEST_REJECTED"],
    "401": ["UNAUTHENTICATED"],
    "403": ["FORBIDDEN"],
    "404": ["NOT_FOUND"],
    "422": ["VALIDATION_FAILED"],
    "500": ["INTERNAL_ERROR"],
    "502": ["DEPENDENCY_UNAVAILABLE"],
    "503": ["DEPENDENCY_UNAVAILABLE"],
    "504": ["DEPENDENCY_UNAVAILABLE"],
}


def _problem_schemas() -> dict[str, Any]:
    """Esquemas `ProblemDetail` e `ProblemFieldError` no formato de `components.schemas`"""
    schema = ProblemDetail.model_json_schema(ref_template="#/components/schemas/{model}")
    definitions = schema.pop("$defs", {})
    return {"ProblemDetail": schema, **definitions}


def _document_errors(operation: dict[str, Any]) -> None:
    """Aplica o `ProblemDetail` a toda resposta 4xx/5xx, documenta o 500 e lista os `errorCode` da operação"""
    responses = operation.setdefault("responses", {})
    responses.setdefault("500", {"description": "Erro interno inesperado"})
    if "422" in responses:
        responses["422"]["description"] = "Corpo ou parâmetro inválido"
    codes: list[str] = []
    for status, response in responses.items():
        if status.startswith(("4", "5")):
            response["content"] = {"application/problem+json": {"schema": dict(_PROBLEM_REF)}}
            codes += _CODES_BY_STATUS.get(status, [])
            if status == "422" and "requestBody" in operation:
                codes.append("MALFORMED_REQUEST")
    operation["x-error-codes"] = list(dict.fromkeys(codes))


def build_openapi(app: FastAPI, include_internal: bool) -> dict[str, Any]:
    """Gera o contrato do serviço; o contrato servido em `/openapi.json` não tem as rotas `/internal/`"""
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
        contact=app.contact,
        license_info=app.license_info,
    )
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)
    schemas.update(_problem_schemas())
    schema["security"] = [{"bearerAuth": []}]
    for path in schema["paths"].values():
        for operation in path.values():
            _document_errors(operation)
    if not include_internal:
        schema["paths"] = {p: v for p, v in schema["paths"].items() if not p.startswith("/internal/")}
        used = {tag for path in schema["paths"].values() for op in path.values() for tag in op.get("tags", [])}
        schema["tags"] = [tag for tag in schema.get("tags", []) if tag["name"] in used]
    return schema


def install_openapi(app: FastAPI) -> None:
    """Troca o gerador padrão do FastAPI pelo contrato público, calculado uma vez"""

    def public_openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = build_openapi(app, include_internal=False)
        return app.openapi_schema

    app.openapi = public_openapi
