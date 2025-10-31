# ------- 1. builder -------
FROM python:3.11-bullseye as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential swig libssl-dev libffi-dev python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Official PyPI source distribution (2.10.3.2)
RUN curl -L -o swisseph-2.10.3.2.tar.gz \
    https://files.pythonhosted.org/packages/source/s/swisseph/swisseph-2.10.3.2.tar.gz && \
    tar xzf swisseph-2.10.3.2.tar.gz && \
    cd swisseph-2.10.3.2 && \
    python setup.py bdist_wheel --dist-dir /wheels

# Rest of wheels
COPY requirements.txt /tmp/
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt
