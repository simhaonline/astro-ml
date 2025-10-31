FROM python:3.11-bullseye

# 1. System deps for swisseph + pip wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libssl-dev \
    libffi-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Python deps (kept in requirements.txt)
COPY requirements.txt swisseph-2.10.3.2.tar.gz ./
RUN pip install --no-cache-dir swisseph-2.10.3.2.tar.gz && \
    pip install --no-cache-dir -r requirements.txt

# 3. App code
COPY . .
USER nobody
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8888"]
