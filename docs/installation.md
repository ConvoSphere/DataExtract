# Installation Guide

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- UV Package Manager (recommended)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-file-extractor-api
cd universal-file-extractor-api

# Start with Docker Compose
docker-compose up -d

# Or for production
docker-compose -f docker-compose.prod.yml up -d

# Or for testing with full monitoring
docker-compose -f docker-compose.test.yml up -d
```

### Option 2: Local Development

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install pre-commit hooks
uv pip install pre-commit
pre-commit install

# Start the application
uv run uvicorn app.main:app --reload
```

## Environment Configuration

### Environment Variables

```bash
# API Configuration
DEBUG=false
LOG_LEVEL=INFO
MAX_FILE_SIZE=157286400  # 150MB
ENABLE_ASYNC_PROCESSING=true

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Worker Configuration
MAX_CONCURRENT_EXTRACTIONS=10
WORKER_PROCESSES=4

# Monitoring
ENABLE_OPENTELEMETRY=true
JAEGER_HOST=jaeger
JAEGER_PORT=6831
```

### Production Settings

For production deployment, use the following settings:

```bash
# Security
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_REQUEST_LOGGING=true

# Performance
MAX_CONCURRENT_EXTRACTIONS=20
WORKER_PROCESSES=8

# Monitoring
ENABLE_OPENTELEMETRY=true
ENABLE_METRICS=true
```

## Docker Deployment Options

### Development Environment

```bash
docker-compose up -d
```

**Services:**
- API Server (port 8000)
- Redis (port 6379)
- Celery Worker
- Celery Beat
- Flower (port 5555)

### Testing Environment

```bash
docker-compose -f docker-compose.test.yml up -d
```

**Additional Services:**
- Jaeger (port 16686)
- Prometheus (port 9090)
- Grafana (port 3000)
- Elasticsearch (port 9200)
- Kibana (port 5601)
- Filebeat

### Production Environment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Production Features:**
- Security hardening
- Resource limits
- Read-only containers
- Health checks
- Monitoring and logging
- SSL/TLS support

## Verification

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Monitoring Dashboards

- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686
- Kibana: http://localhost:5601

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports are already in use
2. **Memory issues**: Increase Docker memory limits
3. **Permission errors**: Check file permissions for logs and temp directories

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api
docker-compose logs worker

# Follow logs in real-time
docker-compose logs -f
```

### Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (data will be lost)
docker-compose down -v

# Remove all containers and images
docker system prune -a
```
