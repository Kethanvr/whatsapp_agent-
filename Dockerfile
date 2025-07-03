# WhatsApp AI Agent - Production Docker Image
# Multi-stage build for minimal image size

# ==========================================
# Stage 1: Go Builder for WhatsApp Bridge
# ==========================================
FROM golang:1.23-alpine AS go-builder

# Install dependencies for Go build
RUN apk add --no-cache git gcc musl-dev sqlite-dev

# Set working directory for Go app
WORKDIR /go/src/whatsapp-bridge

# Copy Go module files
COPY whatsapp-mcp/whatsapp-bridge/ ./

# Download Go dependencies (this will generate or update go.sum if needed)
RUN go mod download

# Ensure go.sum is fully populated (fetches any missing checksums)
RUN go mod tidy

# Build the Go binary with optimizations
RUN CGO_ENABLED=1 GOOS=linux go build -a -ldflags '-extldflags "-static"' -o whatsapp-bridge .

# ==========================================
# Stage 2: Python Builder
# ==========================================
FROM python:3.11-slim AS python-builder

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 3: Production Runtime
# ==========================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy Go binary from builder stage
COPY --from=go-builder /go/src/whatsapp-bridge/whatsapp-bridge /usr/local/bin/

# Copy application code
COPY --chown=appuser:appuser . .

# Copy MCP server code
COPY --chown=appuser:appuser whatsapp-mcp/whatsapp-mcp-server/ ./mcp-server/

# Create necessary directories
RUN mkdir -p logs store data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

    # Copy startup script with execute permissions
    COPY --chmod=755 scripts/start-production.sh /app/start-production.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Expose ports
EXPOSE 3333 3334 8501 8080

# Start command
CMD ["/app/start-production.sh"] 