<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Tradução de campos

O serviço de negócio envia campos de texto. A origem é detectada quando não é informada. O serviço traduz cada campo para os demais idiomas suportados e devolve a resposta ao chamador. O [fluxo entre serviços](https://github.com/Solierrr/docs-warehouse/blob/main/docs/flows/SERVICE_TO_SERVICE_AUTH.md) detalha a autenticação compartilhada.

```mermaid
sequenceDiagram
  participant Core as api-core
  participant API as Serviço de tradução
  participant Google as Google Translation
  Core->>API: POST /internal/i18n/translate (HTTP + X-Service-Key)
  opt Origem não informada
    API->>Google: HTTPS + chave do provedor, detectar idioma
    Google-->>API: Idioma de origem
  end
  API->>Google: HTTPS + chave do provedor, traduzir lote
  alt Tradução concluída
    Google-->>API: Textos traduzidos
    API-->>Core: Idioma de origem e traduções
  else Provedor indisponível
    API-->>Core: Erro de dependência
  end
```

## Casos de erro

Uma chave ausente ou inválida retorna 401 e a chave de outro chamador retorna 403, enquanto uma entrada inválida retorna 422 e uma falha do Google retorna erro de dependência.