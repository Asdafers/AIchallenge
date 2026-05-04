FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY methodic/ ./methodic/
COPY scripts/wp6_mcp_server.py ./scripts/wp6_mcp_server.py
COPY fixtures/ ./fixtures/
COPY docs/schema/ ./docs/schema/

ENV BIGQUERY_DRY_RUN=false

CMD ["sh", "-c", "uvicorn methodic.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
