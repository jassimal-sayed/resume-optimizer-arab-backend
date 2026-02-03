FROM python:3.11-slim

WORKDIR /app

# Copy project metadata
COPY pyproject.toml README.md /app/

# Copy ALL libs (to ensure all dependencies are met)
COPY libs/ /app/libs/

# Copy Service Code
COPY services/gateway_service/ /app/services/gateway_service/

# Install dependencies (editable mode)
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "services.gateway_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
