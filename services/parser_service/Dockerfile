FROM python:3.11-slim

WORKDIR /app

# System Dependencies (OCR)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata
COPY pyproject.toml README.md /app/

# Copy ALL libs
COPY libs/ /app/libs/

# Copy Service Code
COPY services/parser_service/ /app/services/parser_service/

# Install dependencies
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app
EXPOSE 8002

CMD ["uvicorn", "services.parser_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
