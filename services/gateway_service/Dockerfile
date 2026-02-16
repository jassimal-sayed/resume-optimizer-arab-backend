FROM python:3.11-slim

WORKDIR /app

# Install service dependencies only (avoid parser/OCR-heavy deps).
COPY services/gateway_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy app code
COPY libs/ /app/libs/
COPY services/gateway_service/ /app/services/gateway_service/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "services.gateway_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
