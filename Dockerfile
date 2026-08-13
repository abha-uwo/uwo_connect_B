# ==============================================================================
# UWOConnect Backend - GCP Cloud Run / GKE Production Dockerfile
# ==============================================================================

# Build & Runtime Stage
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer outputs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system dependencies (PostgreSQL, build-essential, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn daphne uvicorn

# Copy project source code
COPY . /app/

# Create unprivileged non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose Cloud Run default port
EXPOSE 8080

# Entrypoint script for database migration & static files + server launch
CMD exec gunicorn core.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
