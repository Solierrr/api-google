import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings
from app.errors import ApiError

_service_key_header = APIKeyHeader(name="X-Service-Key", scheme_name="serviceKey", auto_error=False)


def require_caller(*callers: str) -> Callable[..., str]:
    """Dependência que exige o `X-Service-Key` de um dos serviços chamadores aceitos na rota

    Args:
        callers: nomes dos repositórios chamadores aceitos (ex.: "api-core")

    Returns:
        Uma dependência FastAPI que devolve o nome do chamador autenticado

    Raises:
        ApiError: 401 `UNAUTHENTICATED` se a chave faltar ou não for de nenhum chamador;
            403 `FORBIDDEN` se a chave for de um chamador que a rota não aceita
    """

    def dependency(
        key: Annotated[str | None, Security(_service_key_header)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> str:
        if key:
            for caller, expected in settings.service_keys.items():
                if expected and hmac.compare_digest(key.encode(), expected.encode()):
                    if caller in callers:
                        return caller
                    raise ApiError(403, "FORBIDDEN", "Serviço chamador não autorizado nesta rota.")
        raise ApiError(401, "UNAUTHENTICATED", "Chave de serviço ausente ou inválida.")

    return dependency
