# ---- build stage ----
FROM python:3.11-bullseye as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential swig libssl-dev libffi-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# install Python deps into /opt/venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- runtime stage ----
FROM python:3.11-slim-bullseye

# copy the pre-built venv (contains uvicorn)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .
USER nobody

# use python -m so we never rely on PATH
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "4"]
