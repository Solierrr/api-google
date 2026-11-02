<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Consulta de fuso horário

O cliente envia coordenadas e, se necessário, um instante. O serviço consulta uma base local de fusos e calcula o deslocamento UTC daquele instante, sem chamar o Google.

```mermaid
sequenceDiagram
  participant App as Aplicativo
  participant API as Serviço de localização
  participant Base as Base local de fusos
  App->>API: GET /v1/geo/timezone (JWT)
  API->>Base: Identifica o fuso da coordenada
  alt Fuso encontrado
    Base-->>API: Identificador IANA
    API-->>App: Fuso e deslocamento UTC
  else Fuso indeterminado
    API-->>App: 404
  end
```

## Casos de erro

Coordenadas inválidas retornam 422 e um fuso indeterminado retorna 404, enquanto a falta de JWT válido retorna 401 e a indisponibilidade do JWKS faz a autenticação retornar 503.