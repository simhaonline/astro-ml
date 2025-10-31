# ---- builder stage ----
FROM python:3.11-bullseye as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential swig libssl-dev libffi-dev python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

# official 2.10.3.1 source tarball (AstrOrigin)
RUN curl -L -o swisseph-2.10.3.1.tar.gz \
    https://files.pythonhosted.org/packages/source/s/swisseph/swisseph-2.10.3.1.tar.gz && \
    tar xzf swisseph-2.10.3.1.tar.gz && \
    cd swisseph-* && \
    python setup.py bdist_wheel --dist-dir /wheels

# build remaining wheels
COPY requirements.txt /tmp/
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt
