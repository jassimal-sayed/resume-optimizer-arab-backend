FROM python:3.11-slim

WORKDIR /app

# System Dependencies (OCR)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install parser dependencies only.
COPY services/parser_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy app code
COPY libs/ /app/libs/
COPY services/parser_service/ /app/services/parser_service/

ENV PYTHONPATH=/app
EXPOSE 8002

CMD ["uvicorn", "services.parser_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
