from typing import Any

_DESCRIPTIONS = {
    400: "O Google recusou os parâmetros do pedido",
    401: "Credencial ausente, inválida ou expirada",
    403: "Serviço chamador não autorizado nesta rota",
    404: "Nada encontrado para os parâmetros informados",
    422: "Corpo ou parâmetro inválido",
    502: "O Google respondeu em formato inesperado ou recusou a chave do serviço",
    503: "Google ou api-auth indisponível, ou quota do Google excedida",
    504: "O Google não respondeu a tempo",
}


def error_responses(*statuses: int, descriptions: dict[int, str] | None = None) -> dict[int | str, dict[str, Any]]:
    """Respostas de erro documentadas da operação; o esquema `ProblemDetail` entra na geração do contrato"""
    custom = descriptions or {}
    return {status: {"description": custom.get(status, _DESCRIPTIONS[status])} for status in statuses}
