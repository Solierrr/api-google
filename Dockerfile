FROM python:latest

WORKDIR /app

# CLI do Infisical: no QA do Render os segredos são carregados na partida pelo entrypoint.sh
COPY --from=infisical/cli:0.43.138 /bin/infisical /usr/local/bin/infisical

COPY pyproject.toml .
COPY version.txt .
COPY app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
