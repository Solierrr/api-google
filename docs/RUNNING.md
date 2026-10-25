# Rodando o Projeto Localmente

Este repositório é Python (FastAPI). O fluxo local padrão: clonar, instalar dependências, preencher `.env` e rodar via `uvicorn` ou Docker.

<p>
  <a href="https://github.com/syvixor/skills-icons">
    <img src="https://skills.syvixor.com/api/icons?i=python,fastapi,docker,googlecloud" height="48" alt="Rodando o Projeto — Python">
  </a>
</p>

## Possíveis Impedimentos

- **Python 3.14+ instalado localmente** (`pyproject.toml`, `requires-python = ">=3.14"`).
- **Chaves de API**, o `.env.example` lista `GOOGLE_KEY_MAPS`/`GOOGLE_KEY_TRANSLATION`/`GOOGLE_CALENDAR_OAUTH_*` vazias — em produção elas vêm do [Infisical](https://infisical.com), localmente precisam ser preenchidas num `.env` próprio.
- **`api-auth` rodando** (ou apontado via `JWT_JWKS_URL`) para chamar `/v1/address` e `/v1/geo`, que exigem o JWT do usuário; nenhuma capability atual grava em outro serviço.
- **Chaves de serviço**, `SERVICE_KEY_API_CORE` e `SERVICE_KEY_AI_GEOGRAPHIC` (mínimo 32 caracteres) para chamar as rotas `/internal` com `X-Service-Key`; vazias, o chamador é recusado.

## Instalação do Projeto

### Iniciando o repositório com o Github

<p>
  <a href="https://github.com/syvixor/skills-icons">
    <img src="https://skills.syvixor.com/api/icons?i=github,vscode" height="48" alt="Frameworks">
  </a>
</p>

```Comandos para clonar o repositório
git clone https://github.com/Solierrr/google-registry.git
cd ./google-registry
code . -r
```

### Instalando dependências e rodando

<p>
  <a href="https://github.com/syvixor/skills-icons">
    <img src="https://skills.syvixor.com/api/icons?i=python" height="48" alt="Frameworks">
  </a>
</p>

```Comandos para instalação e start local
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

copy .env.example .env
:: preencher as chaves do .env antes de rodar

uvicorn app.main:app --reload
```

Com o serviço no ar, o Swagger fica em `http://localhost:8000/docs` e o contrato em `/openapi.json` (`DOCS_ENABLED=false` desliga os dois). Origens do CORS em `CORS_ALLOWED_ORIGINS`.

### Testes

```Comando de teste
pytest tests --cov=app
```

### Contrato OpenAPI

```Comando de exportação
make openapi
```

Gera o `openapi.yaml` da raiz, com as rotas `/internal`, sem precisar de `.env`. O CI falha se o arquivo versionado não bater com o código.

### Subindo via Docker

<p>
  <a href="https://github.com/syvixor/skills-icons">
    <img src="https://skills.syvixor.com/api/icons?i=docker" height="48" alt="Docker">
  </a>
</p>

```Comando de build e run
docker build -t google-registry .
docker run --env-file .env -p 8000:8000 google-registry
```
