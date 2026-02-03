FROM python:3.11-slim

WORKDIR /app

# Copy project metadata
COPY pyproject.toml README.md /app/

# Copy ALL libs
COPY libs/ /app/libs/

# Copy Service Code
COPY services/orchestrator_service/ /app/services/orchestrator_service/

# Install dependencies
RUN pip install --no-cache-dir -e .

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "services.orchestrator_service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]