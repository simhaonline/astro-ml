# ------- 1. builder -------
FROM python:3.11-bullseye as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential swig libssl-dev libffi-dev python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Download & unpack official 2.10.3.2
RUN curl -L https://github.com/astrorigin/swisseph/archive/refs/tags/v2.10.3.2.tar.gz | tar xz && \
    cd swisseph-* && \
    python setup.py bdist_wheel --dist-dir /wheels

# Rest of wheels
COPY requirements.txt /tmp/
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt

# ------- 2. runtime -------
FROM python:3.11-slim-bullseye
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --find-links /wheels swisseph==2.10.3.2 -r /tmp/requirements.txt && rm -rf /wheels
WORKDIR /app
COPY . .
USER nobody
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "4"]
