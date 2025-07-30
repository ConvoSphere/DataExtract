# Multi-stage build für optimierte Docker-Images
FROM python:3.11-slim as builder

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Poetry installieren
RUN pip install poetry

# Poetry-Konfiguration (keine virtuelle Umgebung in Container)
RUN poetry config virtualenvs.create false

# Dependencies kopieren und installieren
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Produktions-Image
FROM python:3.11-slim as production

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Python-Packages aus Builder-Stage kopieren
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Anwendungscode kopieren
COPY app/ ./app/
COPY README.md ./

# Nicht-Root-User erstellen
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Port exponieren
EXPOSE 8000

# Health-Check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Anwendung starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Development-Image
FROM python:3.11-slim as development

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry installieren
RUN pip install poetry

# Poetry-Konfiguration
RUN poetry config virtualenvs.create false

# Dependencies kopieren und installieren (inkl. Dev-Dependencies)
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi

# Anwendungscode kopieren
COPY . .

# Port exponieren
EXPOSE 8000

# Development-Server starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]