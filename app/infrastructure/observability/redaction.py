"""
Oculta a chave de API do Google (parâmetro de query `key`) em spans e logs das chamadas HTTP

Chave de API na URL -> sem redação ela vai para o trace, para o log e para o collector | o modelo do
setup_observability só redige parâmetros conhecidos, e `key` não está entre eles

Plugado no setup_observability como request_hook/async_request_hook do httpx e, junto, silencia os loggers
httpx/httpcore que registram a URL completa
"""

import logging
import re
from typing import Any

from opentelemetry import trace

# Loggers que registram a URL completa das chamadas (inclusive a chave de API quando ela vai na query)
_URL_LOGGING_LOGGERS = ("httpx", "httpcore")

_KEY_QUERY_PARAM = re.compile(r"([?&]key=)[^&#]*", re.IGNORECASE)


def redact_api_key(url: str) -> str:
    """Troca o valor do parâmetro de query `key` (chave de API do Google) por `REDACTED`"""
    return _KEY_QUERY_PARAM.sub(r"\1REDACTED", url)


def redact_url_in_span(span: trace.Span, request: Any) -> None:
    """Hook de request do httpx: reescreve a URL registrada no span sem a chave de API

    O instrumentation do httpx grava a URL completa (`url.full`/`http.url`) e só redige
    parâmetros conhecidos, entre os quais não está `key`.
    """
    url = redact_api_key(str(request.url))
    span.set_attribute("url.full", url)
    span.set_attribute("http.url", url)


async def async_redact_url_in_span(span: trace.Span, request: Any) -> None:
    """Versão assíncrona de `redact_url_in_span`, usada pelos `httpx.AsyncClient`"""
    redact_url_in_span(span, request)


def silence_url_loggers() -> None:
    """Rebaixa httpx/httpcore para WARNING | em INFO eles logam a URL com a chave de API"""
    for name in _URL_LOGGING_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
