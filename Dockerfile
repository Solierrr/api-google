FROM python:latest

WORKDIR /app

# CLI do Infisical: no QA do Render os segredos são carregados na partida pelo entrypoint.sh
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' | bash \
    && apt-get update && apt-get install -y infisical \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY version.txt .
COPY app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
