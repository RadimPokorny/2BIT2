# Global argument for Python version
ARG PYTHON_VERSION=3.14-slim

# --- STAGE 1: check ---
FROM python:${PYTHON_VERSION} AS check
WORKDIR /src
RUN apt-get update && apt-get install -y php-cli php-xml php-mbstring composer libxml2-dev libxslt-dev gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir ruff~=0.14.4 mypy~=1.19.1 lxml-stubs pydantic pydantic-xml[lxml]
RUN composer global require phpstan/phpstan squizlabs/php_codesniffer --no-interaction \
    && ln -s /root/.composer/vendor/bin/phpstan /usr/local/bin/phpstan \
    && ln -s /root/.composer/vendor/bin/phpcs /usr/local/bin/phpcs
ENTRYPOINT ["/bin/bash"]

# --- STAGE 2: runtime (Interpret) ---
FROM python:${PYTHON_VERSION} AS runtime
WORKDIR /src
RUN apt-get update && apt-get install -y libxml2 libxslt1.1 libxml2-dev libxslt-dev gcc zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY int/requirements.txt ./int/
RUN pip install --no-cache-dir -r ./int/requirements.txt
RUN apt-get purge -y libxml2-dev libxslt-dev gcc zlib1g-dev && apt-get autoremove -y
COPY int/ ./int/
WORKDIR /src
ENTRYPOINT ["python3", "-u", "/src/int/src/solint.py"]

# --- STAGE 3: test (Tester) ---
FROM runtime AS test
RUN apt-get update && apt-get install -y php-cli php-xml php-mbstring composer && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY tester/ ./tester/
RUN if [ -f tester/composer.json ]; then cd tester && composer install --no-dev; fi
COPY /tester/sol_to_xml.py ./
ENTRYPOINT ["php", "/src/tester/src/tester.php"]