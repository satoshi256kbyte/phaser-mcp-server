# Dockerfile for Phaser MCP Server
# Based on Python 3.13 slim for a lightweight container

FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the project into the container
WORKDIR /app
COPY . /app

# Install the project and its dependencies
RUN uv sync --frozen --no-dev

FROM python:3.13-slim

# Install runtime dependencies and create application user
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -r app && \
    useradd -r -g app -d /app -s /sbin/nologin app && \
    mkdir -p /app && \
    chown app:app /app

# Copy the virtual environment and project from the builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/phaser_mcp_server /app/phaser_mcp_server

# Make sure we use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run as non-root
USER app

# Environment variables that can be overridden
ENV FASTMCP_LOG_LEVEL=ERROR \
    PHASER_DOCS_TIMEOUT=30 \
    PHASER_DOCS_MAX_RETRIES=3

# Set working directory
WORKDIR /app

# Health check using the built-in command
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD ["phaser-mcp-server", "--health-check"]

# Entry point
ENTRYPOINT ["phaser-mcp-server"]
