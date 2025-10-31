# ----------------------------------------------------------
# 1. Build stage – compile swisseph + Python wheels
# ----------------------------------------------------------
FROM python:3.11-bullseye as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download the **exact** 2.10.3.2 source tarball (GitHub tag)
RUN curl -L -o swisseph-2.10.03.tar.gz \
    https://github.com/aloistr/swisseph/archive/refs/tags/v2.10.03.tar.gz && \
    tar xzf swisseph-2.10.03.tar.gz && \
    cd swisseph-2.10.03 && \
    python setup.py bdist_wheel --dist-dir /wheels

# Build all remaining wheels (numpy, fastapi, etc.)
COPY requirements.txt /tmp/
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt


# ----------------------------------------------------------
# 2. Runtime stage – slim, no build tools
# ----------------------------------------------------------
FROM python:3.11-slim-bullseye

# copy pre-built wheels only
COPY --from=builder /wheels /wheels

# install everything **without** building
RUN pip install --no-cache-dir --find-links /wheels \
    swisseph==2.10.3.2 \
    -r /tmp/requirements.txt && \
    rm -rf /wheels

WORKDIR /app
COPY . .
USER nobody

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import requests,sys;sys.exit(0 if requests.get('http://localhost:8888/health/live').ok else 1)"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "4"]
