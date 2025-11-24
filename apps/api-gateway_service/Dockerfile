FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Copy shared package and install editable
COPY packages/shared /packages/shared

# Copy service metadata and code
COPY apps/api-gateway_service/pyproject.toml /app/pyproject.toml
COPY apps/api-gateway_service/README.md /app/README.md
COPY apps/api-gateway_service/app /app/app

RUN pip install --no-cache-dir -e /packages/shared && \
    pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
