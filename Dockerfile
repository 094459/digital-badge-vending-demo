FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and fonts
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official image (avoids QEMU emulation issues on cross-platform builds)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app ./app
COPY wsgi.py init_db.py ./

# Install dependencies
RUN uv sync --frozen

# Create directories for runtime data
RUN mkdir -p /app/instance /app/app/src/static/uploads /app/app/src/static/badges

# Expose port 8080 (ECS Express Mode default)
EXPOSE 8080

# AWS credentials will be provided via:
# - IAM role (recommended for ECS/EKS)
# - Environment variables at runtime
# - Mounted AWS config volume

# Initialize database at runtime and start gunicorn
# Using timeout of 120s for AI image generation requests
CMD uv run python init_db.py && \
    uv run gunicorn -w 4 -b 0.0.0.0:8080 --timeout 120 wsgi:app
