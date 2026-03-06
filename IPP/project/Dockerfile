ARG PYTHON_VERSION=3.14-slim

# --- check ---
FROM python:3.14-slim AS check
WORKDIR /src

RUN apt-get update && apt-get install -y \
    gcc libxml2-dev libxslt-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
COPY int/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy the files
COPY . .
RUN chmod -R -x . && chmod +x int/src/solint.py
ENTRYPOINT ["/bin/bash"]

# --- build ---
FROM python:${PYTHON_VERSION} AS build
WORKDIR /app
COPY . .

# --- runtime ---
FROM python:${PYTHON_VERSION} AS runtime
WORKDIR /app

# Get the runtime versions
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled packages
COPY --from=check /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=check /usr/local/bin /usr/local/bin

COPY --from=build /app/int ./int
ENTRYPOINT ["python3", "int/src/solint.py"]

# --- test ---
FROM runtime AS test
WORKDIR /app
COPY --from=build /app/tester ./tester
ENTRYPOINT ["python3", "tester/tester.py"]