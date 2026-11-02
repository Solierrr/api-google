<p align="center">
  <img src="../assets/readme/banners/google.png" alt="Google" width="100%">
</p>

# Execução local

## Pré-requisitos

É preciso ter Python 3.14 ou superior, `make` e um shell compatível, além do Infisical CLI autenticado, que fornece o ambiente. As dependências estão no [`pyproject.toml`](https://github.com/Solierrr/api-google/blob/main/pyproject.toml), e o [guia comum de Python](https://github.com/Solierrr/docs-warehouse/blob/main/readme/running/PYTHON.md) complementa estes passos.

## Preparação e comandos

Na raiz do repositório de origem, `make vault` obtém as variáveis da pasta `/google`. O [exemplo de ambiente](https://github.com/Solierrr/api-google/blob/main/.env.example) lista os nomes necessários. A validação de JWT requer o JWKS do serviço de autenticação. As chaves dos chamadores internos precisam ter ao menos 32 caracteres.

```bash
make install
make vault
make dev
make test
make lint
make openapi
```

`make dev` inicia o Uvicorn na porta 8000. `make test` executa pytest, `make lint` verifica Ruff e `make openapi` exporta o contrato sem depender de um arquivo de ambiente. O [Makefile](https://github.com/Solierrr/api-google/blob/main/Makefile) também oferece `make build`, `make doctor` e `make ci`.

## Verificação e falhas comuns

Abra `http://localhost:8000/docs` para testar a API, usando o `/health` para confirmar o processo e o `/ready` para confirmar que os clientes foram criados. As operações de endereço e fuso exigem JWT e as de tradução e energia solar exigem a chave do chamador. Sem a chave do provedor a consulta externa falha, sem JWKS as rotas de usuário respondem que a autenticação está indisponível, e uma chave de serviço curta demais impede a inicialização.