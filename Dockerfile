FROM node:20-alpine

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt \
    && pip install --no-cache-dir --break-system-packages google-cloud-bigquery

COPY . .

RUN adduser -D appuser
USER appuser

ENV PORT=8080
EXPOSE ${PORT}

CMD ["python3", "scripts/wp9_demo_server.py"]
