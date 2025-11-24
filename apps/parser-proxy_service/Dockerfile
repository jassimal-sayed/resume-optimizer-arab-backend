FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY packages/shared /packages/shared

COPY apps/parser-proxy_service/pyproject.toml /app/pyproject.toml
COPY apps/parser-proxy_service/README.md /app/README.md
COPY apps/parser-proxy_service/app /app/app

RUN pip install --no-cache-dir -e /packages/shared && \
    pip install --no-cache-dir -e .

EXPOSE 8010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
