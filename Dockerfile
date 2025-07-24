# Dockerfile for Phaser MCP Server
# Based on Python 3.14 Alpine for a lightweight container

FROM python:3.14-slim AS uv

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Prefer the system python
ENV UV_PYTHON_PREFERENCE=only-system

# Run without updating the uv.lock file like running with `--frozen`
ENV UV_FROZEN=true

# Copy the required files first
COPY pyproject.toml ./

# Python optimization and uv configuration
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and Python package manager
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    openssl \
    curl && \
    curl -sSL https://astral.sh/uv/install.sh | sh && \
    uv pip install uv

# Generate uv-requirements.txt from pyproject.toml
RUN uv pip export --requirements-file uv-requirements.txt

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --require-hashes --requirement uv-requirements.txt --no-cache-dir && \
    uv sync --python 3.14 --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.14 --frozen --no-dev --no-editable

# Make the directory just in case it doesn't exist
RUN mkdir -p /root/.local

FROM python:3.14-slim

# Place executables in the environment at the front of the path and include other binaries
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Install runtime dependencies and create application user
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    groupadd -r app && \
    useradd -r -g app -d /app -s /sbin/nologin app && \
    mkdir -p /app && \
    chown app:app /app

# Copy application artifacts from build stage
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# Get healthcheck script
COPY ./docker-healthcheck.sh /usr/local/bin/docker-healthcheck.sh
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# Run as non-root
USER app

# Environment variables that can be overridden
ENV FASTMCP_LOG_LEVEL=ERROR \
    PHASER_DOCS_TIMEOUT=30 \
    PHASER_DOCS_MAX_RETRIES=3

# When running the container, add --db-path and a bind mount to the host's db file
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 CMD ["docker-healthcheck.sh"]
ENTRYPOINT ["phaser-mcp-server"]