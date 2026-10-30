from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação | instancia unica
    Segredos (`repr=False`) nunca aparecem em logs/repr
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "dev"
    log_level: str = "INFO"

    # Maps Platform-> uma api key fornece Places, Geocoding, Address Validation, Routes e Solar
    google_key_maps: str = Field(..., repr=False)

    # Cloud Translation
    google_key_translation: str = Field(..., repr=False)

    # OAuth 2.0 Authorization Code por técnico
    google_calendar_oauth_client_id: str = Field(..., repr=False)
    google_calendar_oauth_client_secret: str = Field(..., repr=False)
    google_calendar_oauth_redirect_uri: str

    # Validação do JWT RS256 de usuário
    jwt_jwks_url: str = "http://localhost:8081/.well-known/jwks.json"
    jwt_issuer: str = "solaria-auth"

    # repos Solier chamados via HTTP
    auth_base_url: str

    # X-Service-Key de cada serviço chamador aceito (vazio = chamador recusado)
    service_key_api_core: str | None = Field(default=None, repr=False)
    service_key_ai_geographic: str | None = Field(default=None, repr=False)

    @field_validator("service_key_api_core", "service_key_ai_geographic", mode="before")
    @classmethod
    def _validate_service_key(cls, value: str | None) -> str | None:
        """Chave vazia vale como ausente; chave curta impede a partida"""
        if value is None or not str(value).strip():
            return None
        if len(str(value).strip()) < 32:
            raise ValueError("a chave de serviço precisa ter no mínimo 32 caracteres")
        return str(value).strip()

    @property
    def service_keys(self) -> dict[str, str | None]:
        """Chave de cada chamador aceito, pelo nome do repositório"""
        return {"api-core": self.service_key_api_core, "ai-geographic": self.service_key_ai_geographic}


class WebSettings(BaseSettings):
    """Configuração da camada web, lida na importação do app e sem segredos (a exportação do contrato não tem `.env`)"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Swagger em /docs e contrato em /openapi.json; desligado em PROD
    docs_enabled: bool = True

    # Origens aceitas pelo CORS, separadas por vírgula (no QA inclui o web-sandbox)
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        """Origens do CORS sem espaços nem itens vazios"""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância única de `Settings` para o processo atual"""
    return Settings()
