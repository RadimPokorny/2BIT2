# --- check ---
FROM python:3.12-slim AS check
WORKDIR /src
COPY requirements.txt ./
COPY int/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
ENTRYPOINT ["/bin/bash"]

# --- build ---
FROM python:3.12-slim AS build
WORKDIR /app
COPY . .


# --- runtime ---
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=build /app/int ./int
# Entry point for the interpret
ENTRYPOINT ["python3", "int/interpreter.py"]


# --- test ---
FROM runtime AS test
WORKDIR /app
COPY --from=build /app/tester ./tester
ENTRYPOINT ["python3", "tester/tester.py"]