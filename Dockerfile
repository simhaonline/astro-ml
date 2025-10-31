# ------- Dockerfile -------
FROM python:3.11-bullseye

# Install build deps *before* pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy & install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Non-root run
USER nobody

# Health-check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests, sys; sys.exit(0 if requests.get('http://localhost:8888/health/live').ok else 1)"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "4"]
