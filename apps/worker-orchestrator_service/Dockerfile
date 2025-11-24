FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY packages/shared /packages/shared

COPY apps/worker-orchestrator_service/pyproject.toml /app/pyproject.toml
COPY apps/worker-orchestrator_service/README.md /app/README.md
COPY apps/worker-orchestrator_service/app /app/app

RUN pip install --no-cache-dir -e /packages/shared && \
    pip install --no-cache-dir -e .

CMD ["python", "-m", "app.main"]
