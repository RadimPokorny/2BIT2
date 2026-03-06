# Global argument for Python version
ARG PYTHON_VERSION=3.14-slim

# --- STAGE 1: check (Static analysis & Linting) ---
FROM python:${PYTHON_VERSION} AS check
WORKDIR /src

# Install system dependencies required for building lxml and other C-extensions
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first to leverage Docker layer caching
COPY requirements.txt ./
COPY int/requirements-dev.txt ./
# Copy pyproject.toml (assuming it's in the root or int/ directory)
COPY int/pyproject.toml ./

# Install all dependencies including dev tools (ruff, mypy)
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# IMPORTANT: Copy the source code BEFORE running chmod
COPY . .

# Fix permissions:
# 1. Remove executable bit from ALL files to satisfy Ruff EXE002
# 2. Restore execution right ONLY for the entry point script
RUN find . -type f -exec chmod -x {} + && \
    chmod +x int/src/solint.py

# Default command is bash to allow manual tool execution
ENTRYPOINT ["/bin/bash"]


# --- STAGE 2: build (Preparation of source) ---
FROM python:${PYTHON_VERSION} AS build
WORKDIR /app
# Copy project files for the final image
COPY . .


# --- STAGE 3: runtime (The actual Interpreter) ---
FROM python:${PYTHON_VERSION} AS runtime
WORKDIR /app

# Install only runtime shared libraries (no compilers needed here)
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from the check stage
COPY --from=check /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=check /usr/local/bin /usr/local/bin

# Copy the application source from build stage
COPY --from=build /app/int ./int

# Set the interpreter entry point
ENTRYPOINT ["python3", "int/src/solint.py"]


# --- STAGE 4: test (Running automated tests) ---
FROM runtime AS test
WORKDIR /app
# Copy test suite into the runtime-based image
COPY --from=build /app/tester ./tester
ENTRYPOINT ["python3", "tester/tester.py"]