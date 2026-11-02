<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Arquitetura

O servidor FastAPI separa os contratos de domínio, a orquestração, os adaptadores e as rotas HTTP, criando os clientes HTTP na inicialização. Endereços, tradução e energia solar usam as APIs do Google, o fuso horário usa uma base local e o serviço não tem banco próprio.

```mermaid
flowchart LR
  Clientes[Aplicativo e serviços] -->|HTTP + JWT ou X-Service-Key| API[Rotas FastAPI]
  API --> Aplicacao[Serviços de aplicação]
  Aplicacao --> Portas[Portas de domínio]
  Portas --> Adaptadores[Adaptadores]
  Adaptadores -->|HTTPS + chave do provedor| Google[APIs Google]
  Adaptadores --> Fusos[Base local de fusos]
  API -->|HTTPS + JWKS| Auth[api-auth]
```

## Pastas

| Pasta | Papel |
|---|---|
| `app/api/routers/` | Rotas, autenticação e validação de entrada. |
| `app/application/` | Casos de uso por capacidade. |
| `app/domain/` | Contratos dos provedores. |
| `app/infrastructure/google/` | Adaptação das APIs externas. |
| `app/infrastructure/http/` | Clientes com timeout e repetição. |
| `app/infrastructure/auth/` | JWT e chaves de serviço. |
| `app/infrastructure/geo/` | Fusos locais. |
| `app/schemas/` | Modelos de entrada e saída. |

## Integrações

| Relação | Protocolo | Autenticação |
|---|---|---|
| Aplicativo e portal de QA → serviço | HTTP | JWT de usuário. |
| `api-core` → tradução | HTTP | `X-Service-Key`. |
| `ai-geographic` → energia solar | HTTP | `X-Service-Key`. |
| Serviço → `api-auth` | HTTP | JWKS público para validar JWT. |
| Serviço → APIs Google | HTTPS | Chave do provedor. |

O cliente de token do Calendar existe, mas nenhuma rota o usa ainda, e o Calendar faz parte do escopo do serviço. O [fluxo compartilhado](https://github.com/Solierrr/docs-warehouse/blob/main/docs/flows/SERVICE_TO_SERVICE_AUTH.md) descreve chamadas entre serviços.

## Decisões e operação

O `AddressService` combina Places, Geocoding e Address Validation. Uma falha na validação durante a resolução mantém o endereço e devolve `validation: null`. O `TranslationService` agrupa textos por idioma de destino. O cliente Google repete falhas transitórias até três vezes nas operações permitidas. `tzfpy` e `ZoneInfo` calculam fusos sem consumir quota externa.

O `/health` informa a versão lida de `version.txt`, e o `/ready` confere se os clientes HTTP foram criados, sem chamar o Google. O OpenTelemetry registra traces, logs e métricas com a chave ocultada nas URLs, e o contrato público esconde o caminho `/internal`, que só aparece no contrato exportado.