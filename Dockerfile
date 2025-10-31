# ----------------------------------------------------------
# 1. Builder stage – compile all wheels (incl. pyswisseph)
# ----------------------------------------------------------
FROM python:3.11-bullseye as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential swig libssl-dev libffi-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# create venv & build wheels
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt


# ----------------------------------------------------------
# 2. Runtime stage – slim, no build tools
# ----------------------------------------------------------
FROM python:3.11-slim-bullseye

# copy pre-built venv (contains uvicorn, fastapi, pyswisseph, etc.)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .   # installs src/ into venv
USER nobody

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests,sys;sys.exit(0 if requests.get('http://localhost:8888/health/live').ok else 1)"

CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "4"]
