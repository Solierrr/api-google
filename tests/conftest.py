import os

os.environ["GOOGLE_KEY_MAPS"] = "test-google-key-maps"
os.environ["GOOGLE_KEY_TRANSLATION"] = "test-google-key-translation"
os.environ["GOOGLE_CALENDAR_OAUTH_CLIENT_ID"] = "test-calendar-client-id"
os.environ["GOOGLE_CALENDAR_OAUTH_CLIENT_SECRET"] = "test-calendar-client-secret"
os.environ["GOOGLE_CALENDAR_OAUTH_REDIRECT_URI"] = "http://localhost:8000/calendar/callback"
os.environ["AUTH_BASE_URL"] = "http://localhost:8081"
os.environ["LLM_PROBE_INTERVAL_SECONDS"] = "0"
os.environ["SERVICE_KEY_API_CORE"] = "test-service-key-api-core-0000000000"
os.environ["SERVICE_KEY_AI_GEOGRAPHIC"] = "test-service-key-ai-geographic-00000"

import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """Limpa o cache do get_settings() antes e depois de cada teste

    get_settings() usa @lru_cache, então sem essa limpeza um teste que
    altera configurações vazaria o estado para os testes seguintes.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _no_retry_backoff(monkeypatch):
    """Elimina a espera entre as tentativas do `GoogleHttpClient`, para os testes de retry não demorarem"""
    from app.infrastructure.http.google_http_client import GoogleHttpClient

    async def no_sleep(self, attempt):
        return None

    monkeypatch.setattr(GoogleHttpClient, "_sleep_backoff", no_sleep)


@pytest.fixture
def anonymous_client():
    """Cliente HTTP de teste da aplicação FastAPI (roda o lifespan, sem I/O real na criação dos clients)"""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(anonymous_client):
    """Cliente de teste com um usuário autenticado (o JWT é validado nos testes de `bearer_auth`)"""
    from app.infrastructure.auth.bearer_auth import require_authenticated_user
    from app.main import app

    app.dependency_overrides[require_authenticated_user] = lambda: "user-1"
    yield anonymous_client
    app.dependency_overrides.pop(require_authenticated_user, None)
