# Railway-optimized Dockerfile for Live Transcription Service
# Multi-stage build for efficiency and smaller final image

# Stage 1: Builder Stage - CPU-only for Railway (no CUDA)
FROM python:3.11-slim AS builder

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal build dependencies for Railway
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    pkg-config \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# PyTorch will be installed by RealtimeSTT with correct versions

# Skip DeepSpeed for Railway deployment (not needed for basic transcription)
# DeepSpeed requires GPU and adds significant complexity and size

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install remaining Python dependencies from requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt \
    || (echo "pip install -r requirements.txt FAILED." && exit 1)

# Copy the application code
COPY code/ ./code/

# --- Stage 2: Runtime Stage for Railway ---
# Lightweight Python runtime without CUDA
FROM python:3.11-slim

# Railway-optimized environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    RAILWAY_DEPLOYMENT=true \
    MAX_AUDIO_QUEUE_SIZE=30 \
    LOG_LEVEL=INFO

# Install minimal runtime dependencies for Railway
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for the application
WORKDIR /app/code

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application code from the builder stage
COPY --from=builder /app/code /app/code

# Railway-optimized model pre-loading (minimal for faster startup)
# Skip heavy model downloads in container build - let them load at runtime

# Set minimal environment variables for Railway
ENV HOME=/root
ENV PYTHONPATH=/app/code
ENV HF_HOME=/tmp/.cache/huggingface
ENV TORCH_HOME=/tmp/.cache/torch
ENV RUNNING_IN_DOCKER=true
ENV PORT=8000

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/status || exit 1

# Expose the port (Railway sets PORT environment variable)
EXPOSE ${PORT}

# Railway deployment optimizations - direct command without entrypoint
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--access-log"]
