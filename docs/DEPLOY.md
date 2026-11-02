<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Publicação

## Ambientes

| Ambiente | Endereço | Observação |
|---|---|---|
| Local | `http://localhost:8000` | Iniciado por `make dev`. |
| QA | [Render](https://google-registry.onrender.com) | URL declarada no contrato OpenAPI. |
| PROD | Acesso interno no GKE | `ClusterIP`, sem Ingress próprio |

Os procedimentos comuns estão em [QA no Render](https://github.com/Solierrr/docs-warehouse/blob/main/readme/deploy/QA_RENDER.md) e [PROD no GKE](https://github.com/Solierrr/docs-warehouse/blob/main/readme/deploy/PROD_GKE_ARGOCD.md). O [Dockerfile](https://github.com/Solierrr/api-google/blob/main/Dockerfile) instala o pacote e inicia o Uvicorn na porta 8000 pelo [`entrypoint.sh`](https://github.com/Solierrr/api-google/blob/main/entrypoint.sh), que, com as credenciais do Infisical presentes, carrega as pastas `/google`, `/service-urls` e `/service-keys` antes da partida, e sem elas inicia direto com as variáveis do ambiente.

## Configuração específica

O ambiente fornece as credenciais do Google, o OAuth do Calendar, o endereço do serviço de autenticação e as chaves dos chamadores, e `DOCS_ENABLED=false` desliga o Swagger e o contrato servido. A prontidão é `/ready` e o processo é verificado por `/health`. O nome oficial do serviço é `api-google`, que substituiu `google-registry`, e as referências antigas ainda aparecem na imagem e no serviço publicado.
