<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# API

## Autenticação e contrato

As rotas `/v1/address` e `/v1/geo` exigem `Authorization: Bearer <token>` com o JWT do `api-auth`, e as rotas `/internal/i18n/translate` e `/internal/solar/roof-viability` exigem a `X-Service-Key` de um chamador permitido, enquanto a saúde e a prontidão são públicas. O [contrato exportado](https://github.com/Solierrr/api-google/blob/main/openapi.yaml) inclui as rotas internas, mas o [Swagger em QA](https://google-registry.onrender.com/docs) e o `/openapi.json` servido mostram apenas as rotas públicas quando a documentação está ligada.

## Operações

| Grupo | Finalidade |
|---|---|
| Endereços | Sugestão, detalhe, geocodificação, validação e resolução. |
| Geografia | Fuso e deslocamento UTC de uma coordenada. |
| Tradução | Detecção do idioma e tradução de campos. |
| Energia solar | Dados solares do telhado mais próximo. |
| Saúde | Estado do processo e prontidão. |

As rotas antigas `/v1/i18n/translate` e `/v1/solar/roof-viability` permanecem abertas e fora do contrato, e saem depois que os chamadores migrarem para as rotas `/internal` com a `X-Service-Key`.

## Erros

Os erros de entrada e de dependência usam `application/problem+json` com `errorCode`, com `UNAUTHENTICATED` para chave inválida, `FORBIDDEN` para chamador não permitido e `UPSTREAM_REQUEST_REJECTED` quando o provedor rejeita o pedido. As falhas externas podem gerar 502, 503 ou 504, conforme o [catálogo de erros](https://github.com/Solierrr/docs-warehouse/blob/main/docs/standards/ERROR_CODES.md), e o `/ready` responde em JSON simples.

## Exemplo local

```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/v1/geo/timezone?latitude=-23.55&longitude=-46.63"
```
