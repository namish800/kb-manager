# KB Management Service Dockerfile
# Multi-stage build using UV with pyproject.toml

FROM python:3.12-slim as builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy UV workspace configuration
COPY pyproject.toml uv.lock ./
COPY packages/kb_ingestion/pyproject.toml packages/kb_ingestion/README.md packages/kb_ingestion/
COPY packages/kb_retriever/pyproject.toml packages/kb_retriever/README.md packages/kb_retriever/
COPY packages/kb_event_handler/pyproject.toml packages/kb_event_handler/README.md packages/kb_event_handler/

# Install dependencies in virtual environment
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim

# Install system dependencies for production
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application source code
COPY --chown=appuser:appuser packages/kb_ingestion/src packages/kb_ingestion/src
COPY --chown=appuser:appuser packages/kb_retriever/src packages/kb_retriever/src  
COPY --chown=appuser:appuser packages/kb_event_handler/src packages/kb_event_handler/src

# Copy workspace configuration
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
COPY --chown=appuser:appuser packages/kb_ingestion/pyproject.toml packages/kb_ingestion/README.md packages/kb_ingestion/
COPY --chown=appuser:appuser packages/kb_retriever/pyproject.toml packages/kb_retriever/README.md packages/kb_retriever/
COPY --chown=appuser:appuser packages/kb_event_handler/pyproject.toml packages/kb_event_handler/README.md packages/kb_event_handler/

# Switch to non-root user
USER appuser

# Make sure we use venv
ENV PATH="/app/.venv/bin:$PATH"

# Set Python path to include all packages
ENV PYTHONPATH="/app/packages/kb_ingestion/src:/app/packages/kb_retriever/src:/app/packages/kb_event_handler/src:$PYTHONPATH"

# Configure application defaults
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV ENVIRONMENT=production
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO
ENV TEMP_DIR=/tmp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${API_PORT}/api/v1/health || exit 1

# Expose port
EXPOSE ${API_PORT}

# Run the FastAPI application
CMD ["python", "-m", "kb_event_handler.main"]