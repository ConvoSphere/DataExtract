# Multi-stage Dockerfile für Universal File Extractor API
FROM python:3.11-slim as base

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    # Build-Tools
    build-essential \
    # System-Libraries
    libmagic1 \
    libtesseract-dev \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    # Audio/Video
    ffmpeg \
    libavcodec-extra \
    # Image Processing
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Archive Tools
    unzip \
    unrar \
    p7zip-full \
    # Network Tools
    curl \
    wget \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# UV installieren
RUN pip install uv

# Arbeitsverzeichnis setzen
WORKDIR /app

# Dependencies kopieren
COPY pyproject.toml uv.lock ./

# Dependencies installieren
RUN uv sync --frozen

# Application Code kopieren
COPY . .

# Development Stage
FROM base as development

# Development Dependencies installieren
RUN uv sync --group dev

# Ports exponieren
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Development Server starten
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production Stage
FROM base as production

# Production-spezifische Optimierungen
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Non-root User erstellen
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Verzeichnisse erstellen und Berechtigungen setzen
RUN mkdir -p /app/temp /app/logs && \
    chown -R appuser:appuser /app

# User wechseln
USER appuser

# Ports exponieren
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production Server starten
CMD ["uv", "run", "gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]

# Worker Stage
FROM production as worker

# Celery Worker starten
CMD ["uv", "run", "celery", "-A", "app.workers.tasks", "worker", "--loglevel=info", "--concurrency=4"]

# Beat Stage
FROM production as beat

# Celery Beat starten
CMD ["uv", "run", "celery", "-A", "app.workers.tasks", "beat", "--loglevel=info"]
