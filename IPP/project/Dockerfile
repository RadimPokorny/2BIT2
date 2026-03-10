# Global argument for Python version
ARG PYTHON_VERSION=3.14-slim

# --- STAGE 1: check ---
# Static analysis
FROM python:${PYTHON_VERSION} AS check
WORKDIR /src

# Python dependency install
RUN apt-get update && apt-get install -y \
    gcc libxml2-dev libxslt-dev zlib1g-dev \
    php-cli php-xml php-mbstring unzip \
    && rm -rf /var/lib/apt/lists/*

# Installing the composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Install the Python tools
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt ruff mypy

# Copying the source code for the static analysis
COPY . .  


# Using terminal with bash
ENTRYPOINT ["/bin/bash"]

# --- STAGE 2: build ---
# Copying our interpreter
FROM python:${PYTHON_VERSION} AS build
WORKDIR /app
COPY int/ ./int/

# --- STAGE 3: build-test ---
# Installing the PHP dependencies and preparing the tester environment
FROM composer:latest AS build-test
WORKDIR /app/tester
COPY tester/composer.json tester/composer.lock* ./
RUN composer install --no-interaction --optimize-autoloader --no-dev
COPY tester/ .

# --- STAGE 4: runtime ---
# Image for the interpreter
FROM python:${PYTHON_VERSION} AS runtime
WORKDIR /app

# Installing the necessery libraries for the Python interpreter
RUN apt-get update && apt-get install -y \
    libxml2 libxslt1.1 zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/int ./int
# Check stages packages for the runtime
COPY --from=check /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

ENTRYPOINT ["python3", "int/src/solint.py"]

# --- STAGE 5: test ---
# Default, but adds the PHP
FROM runtime AS test

# Install the PHP interpreter
RUN apt-get update && apt-get install -y \
    php-cli php-xml php-mbstring \
    && rm -rf /var/lib/apt/lists/*

# Copying the tester with a installed vendor build-test
COPY --from=build-test /app/tester ./tester

ENTRYPOINT ["php", "tester/src/tester.php"]