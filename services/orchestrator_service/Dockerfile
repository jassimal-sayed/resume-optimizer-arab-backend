FROM python:3.11-slim

WORKDIR /app

# Install service dependencies only (avoid parser/OCR-heavy deps).
COPY services/orchestrator_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy app code
COPY libs/ /app/libs/
COPY services/orchestrator_service/ /app/services/orchestrator_service/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "services.orchestrator_service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
