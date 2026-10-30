# Arquitetura do Repositório

FastAPI, arquitetura em camadas por capability (`domain` -> `application` -> `infrastructure` -> `api`), igual em `solar` e `i18n`.

<p>
  <a href="https://github.com/syvixor/skills-icons">
    <img src="https://skills.syvixor.com/api/icons?i=python,fastapi,googlecloud,docker" height="48" alt="Stack do Projeto">
  </a>
</p>

## Camadas

- **`app/domain/<capability>/ports.py`**, contrato (`Protocol`) que a capability espera do provedor Google — nenhum detalhe de HTTP/formato de payload aqui.
- **`app/application/<capability>/service.py`**, orquestra os ports da capability. Não grava nada em outros serviços: devolve o resultado a quem chamou.
- **`app/infrastructure/google/<capability>/adapter.py`**, único lugar que conhece o formato de request/response da API Google real, sobre o `GoogleHttpClient` (`app/infrastructure/http`) compartilhado (timeout, retry/backoff, observabilidade).
- **`app/infrastructure/solier/auth/*_client.py`**, cliente do `api-auth` (tokens do Calendar, ainda sem uso), sobre o `InternalHttpClient` compartilhado, mesma estrutura do `GoogleHttpClient`.
- **`app/api/routers/<capability>.py`**, endpoints FastAPI (`/v1/<capability>/...` para pessoas, `/internal/<capability>/...` para serviços), monta o service via `Depends` a partir dos clients criados no lifespan (`app/api/dependencies.py`).
- **`app/schemas/<capability>.py`**, DTOs públicos (Pydantic) do router.

## Capabilities

- **`address`**, `/v1/address/{suggestions,places/{place_id},geocode,reverse-geocode,validate,resolve}`; três adapters (Places New, Geocoding, Address Validation) atrás de um `AddressService`. `resolve` junta busca e validação; se a validação falhar, o endereço volta com `validation: null`.
- **`solar`**, `/internal/solar/roof-viability` (`buildingInsights:findClosest`), com os dados do painel de referência do Google; chamada pelo `ai-geographic`.
- **`i18n`**, `/internal/i18n/translate`, chamada pelo `api-core`; detecta o idioma de origem (Cloud Translation API, `detect`) e traduz os campos para os outros dois dos três idiomas suportados (`en`/`es`/`pt`), um lote por idioma de destino.
- **`geo`**, `/v1/geo/timezone`; fuso por coordenada via `tzfpy`, sem API externa.

## Observabilidade e autenticação

- **OpenTelemetry** (`app/infrastructure/observability`): `setup_observability` liga traces, métricas HTTP e logs (console + OTLP) do modelo SOLIER; span por chamada Google/interna e métricas de chamadas (contador + histograma de duração, por capability/serviço) ficam em `metrics.py`; `redaction.py` oculta a chave `key=` nos spans e logs.
- **JWT RS256** (`app/infrastructure/auth/bearer_auth.py`, esquema `bearerAuth`), valida o token de usuário emitido pelo `api-auth` via JWKS; exigido em `/v1/address` e `/v1/geo`, chamadas pelo `mobile-app`.
- **Chave de serviço** (`app/infrastructure/auth/service_key.py`, esquema `serviceKey`), cabeçalho `X-Service-Key` comparado em tempo constante com `SERVICE_KEY_<CHAMADOR>`; cada rota `/internal` declara os chamadores aceitos (`require_caller`). Chave ausente ou inválida dá 401, chamador não aceito dá 403, e chave com menos de 32 caracteres impede a partida.
- **Transição**: `/v1/i18n/translate` e `/v1/solar/roof-viability` continuam respondendo sem credencial, fora do contrato, só até o `api-core` e o `ai-geographic` passarem a chamar as rotas `/internal` com a chave; depois saem.

## Contrato e erros

- **Erros** (`app/errors.py`), todo 4xx e 5xx sai em `application/problem+json` (`type`, `title`, `status`, `errorCode`, `detail`, `instance`, `timestamp`, `traceId` e `errors` na validação). As exceptions do Google e do `api-auth` declaram o próprio `errorCode` (`app/exceptions`).
- **OpenAPI** (`app/openapi.py`), Swagger em `/docs` e contrato em `/openapi.json`, desligados com `DOCS_ENABLED=false` (PROD). O contrato servido não tem as rotas `/internal`; o `openapi.yaml` da raiz tem, e é gerado por `make openapi` e conferido no CI.
- **Versão**, `version.txt` (atualizado pelo release-please) lido por `app/version.py`, usado no FastAPI, no contrato e no `/health`.
- **Saúde**, `/health` (vivo, com a versão) e `/ready` (pronto: clientes HTTP criados); o serviço não guarda estado, então o pronto não consulta o Google.

## Containerização

- `Dockerfile` copia o `version.txt`, instala a partir de `pyproject.toml` (`pip install .`) e sobe `uvicorn app.main:app` na porta `8000`.

```Tree do Repositório
├── app/
│   ├── api/            # routers + dependencies FastAPI
│   ├── application/    # services por capability
│   ├── domain/          # ports (contratos) por capability
│   ├── exceptions/       # hierarquia de exceptions (ApiError do modelo de erro)
│   ├── infrastructure/
│   │   ├── auth/         # JWT/JWKS do api-auth
│   │   ├── google/       # adapters por capability
│   │   ├── http/         # clients HTTP compartilhados (Google/interno)
│   │   ├── observability/ # setup OTEL, erros ProblemDetail, métricas e redação
│   │   ├── geo/          # fuso horário local
│   │   └── solier/       # cliente do api-auth
│   ├── schemas/          # DTOs por capability
│   ├── config.py
│   └── main.py
├── tests/
├── Dockerfile
├── pyproject.toml
└── sonar-project.properties
```
