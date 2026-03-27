# Global argument for Python version
ARG PYTHON_VERSION=3.14-slim

# --- STAGE 1: check ---
FROM python:${PYTHON_VERSION} AS check
WORKDIR /src
RUN apt-get update && apt-get install -y \
    php-cli php-xml php-mbstring composer \
    libxml2-dev libxslt-dev gcc \
    && rm -rf /var/lib/apt/lists/*
COPY int/requirements.txt ./int/
COPY int/ ./int/
RUN pip install --no-cache-dir \
    -r ./int/requirements.txt \
    ruff~=0.14.4 \
    mypy~=1.19.1 \
    lxml-stubs
RUN ln -sf $(which ruff) /src/ruff && \
    ln -sf $(which mypy) /src/mypy
ENTRYPOINT ["/bin/bash"]

# --- STAGE 2: build ---
FROM python:${PYTHON_VERSION} AS build
WORKDIR /app
COPY int/ ./int/

# --- STAGE 3: build-test ---
FROM php:8.3-cli AS build-test
WORKDIR /app
COPY tester/ ./tester/

# --- STAGE 4: runtime ---
FROM python:${PYTHON_VERSION} AS runtime
WORKDIR /src
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*
COPY int/requirements.txt ./int/
RUN pip install --no-cache-dir -r ./int/requirements.txt
COPY --from=build /app/int ./int
ENTRYPOINT ["python3", "int/src/solint.py"]

# --- STAGE 5: test ---
FROM runtime AS test
RUN apt-get update && apt-get install -y \
    php-cli php-xml php-mbstring \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build-test /app/tester ./tester

ENTRYPOINT ["php", "tester/src/tester.php"]