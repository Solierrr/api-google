<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Consulta de endereço

A pessoa informa um texto ou escolhe uma sugestão. O serviço consulta Places ou Geocoding, estrutura o endereço e tenta validá-lo. O resultado volta para o cliente sem ser salvo neste serviço.

```mermaid
sequenceDiagram
  participant App as Aplicativo
  participant API as Serviço de localização
  participant Places as Google Places
  participant Geo as Google Geocoding
  participant Valid as Google Address Validation
  App->>API: POST /v1/address/resolve (JWT)
  alt Lugar escolhido
    API->>Places: HTTPS + chave do provedor
    Places-->>API: Endereço e coordenadas
  else Texto livre
    API->>Geo: HTTPS + chave do provedor
    Geo-->>API: Endereço e coordenadas
  end
  API->>Valid: HTTPS + chave do provedor
  alt Validação disponível
    Valid-->>API: Parecer
    API-->>App: Endereço e parecer
  else Falha na validação
    API-->>App: Endereço sem parecer
  end
```

## Casos de erro

Um lugar ou texto sem resultado retorna 404, um JWT ausente ou inválido retorna 401 e uma falha de localização no provedor retorna erro de dependência. Quando a validação falha depois de o endereço ter sido localizado, o endereço encontrado não é descartado.