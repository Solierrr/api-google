<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Situação verificada em 2026-10-30

## Em funcionamento

- Em 2026-10-30, as rotas de endereço, fuso, tradução e energia solar estão implementadas na `main`.
- Em 2026-10-30, as rotas de usuário validam JWT e as rotas internas validam `X-Service-Key`.
- Em 2026-10-30, o contrato OpenAPI é exportado do código e há testes de rotas, serviços e adaptadores.

## Limitações

- Em 2026-10-30, duas rotas antigas permanecem abertas até a migração dos chamadores para `/internal`.
- Em 2026-10-30, o cliente de token do Calendar ainda não é usado por uma rota, embora as configurações de OAuth sejam exigidas, e o Calendar faz parte do escopo do serviço.
- Em 2026-10-30, o acesso de PROD é interno ao cluster, por `ClusterIP`.
- Em 2026-10-30, o nome oficial é `api-google`, e a imagem e o serviço publicado ainda trazem o nome antigo `google-registry`.
- Em 2026-10-30, o `Dockerfile` usa `python:latest` e o `pyproject.toml` exige Python 3.14 ou superior.
