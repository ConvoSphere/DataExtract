# File Extractor Microservice

## Übersicht

Der File Extractor ist als Microservice konzipiert, der in eine bestehende Infrastruktur eingebettet wird. Die externe Infrastruktur (Prometheus, Grafana, ELK Stack) wird zentral bereitgestellt.

## Architektur

### Komponenten

1. **API Server** (`api`): FastAPI-basierte REST API
2. **Worker** (`worker`): Celery-Worker für asynchrone Verarbeitung
3. **Beat** (`beat`): Celery-Beat für geplante Tasks
4. **Redis** (`redis`): Job-Queue und Cache
5. **Flower** (`flower`): Celery-Monitoring (optional, nur Debug)

### OpenTelemetry Integration

Der Microservice ist vollständig mit OpenTelemetry instrumentiert:

- **Distributed Tracing**: Automatische Span-Erstellung für HTTP-Requests und Extraktionen
- **Custom Metrics**: Business-spezifische Metriken für Extraktionen
- **Structured Logging**: JSON-basiertes Logging mit Trace-Korrelation
- **OTLP Export**: Export zu zentraler OpenTelemetry-Infrastruktur

## Konfiguration

### Umgebungsvariablen

```bash
# OpenTelemetry
OTLP_ENDPOINT=http://otel-collector:4317
ENABLE_OPENTELEMETRY=true
ENABLE_METRICS=true
ENABLE_TRACING=true

# Service-Identifikation
SERVICE_NAME=file-extractor
SERVICE_VERSION=0.1.0
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true
ENABLE_EXTRACTION_LOGGING=true

# Redis
REDIS_URL=redis://redis:6379

# Dateiverarbeitung
MAX_FILE_SIZE=157286400
ENABLE_ASYNC_PROCESSING=true
MAX_CONCURRENT_EXTRACTIONS=10
```

### Health Checks

- **Liveness**: `GET /health/live`
- **Readiness**: `GET /health/ready`
- **Health**: `GET /health`

## Monitoring

### Custom Metrics

Der Microservice exportiert folgende Custom Metrics über OpenTelemetry:

#### Counter
- `file_extractions_total`: Gesamtzahl der Extraktionen
- `extraction_errors_total`: Anzahl der Extraktionsfehler
- `file_type_extractions_total`: Extraktionen nach Dateityp

#### Histogram
- `extraction_duration_seconds`: Extraktionsdauer
- `file_size_bytes`: Verarbeitete Dateigrößen

#### UpDownCounter
- `active_jobs`: Aktuell aktive Jobs

### Distributed Tracing

Automatische Span-Erstellung für:
- HTTP-Requests (mit FastAPI-Instrumentation)
- Datei-Extraktionen
- Job-Status-Änderungen
- Redis-Operationen

### Logging

Strukturiertes JSON-Logging mit:
- Trace-ID und Span-ID Korrelation
- Request-Informationen
- Extraktions-Details
- Error-Stack-Traces

## Deployment

### Docker Compose

```bash
# Microservice starten
docker-compose -f docker-compose.microservice.yml up -d

# Mit Debug-Komponenten
docker-compose -f docker-compose.microservice.yml --profile debug up -d
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: file-extractor-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: file-extractor-api
  template:
    metadata:
      labels:
        app: file-extractor-api
    spec:
      containers:
      - name: api
        image: file-extractor:latest
        ports:
        - containerPort: 8000
        env:
        - name: OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        - name: ENABLE_OPENTELEMETRY
          value: "true"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
```

## Integration

### OpenTelemetry Collector

Der Microservice exportiert Daten an einen OpenTelemetry Collector:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

exporters:
  prometheus:
    endpoint: "0.0.0.0:9464"
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, logging]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
```

### Service Mesh Integration

Für Service Mesh (z.B. Istio) Integration:

```yaml
# Service Mesh Annotations
annotations:
  sidecar.istio.io/inject: "true"
  proxy.istio.io/config: |
    tracing:
      sampling: 100
      custom_tags:
        environment:
          literal:
            value: "production"
```

## Bereinigte Komponenten

### Entfernt (wird zentral bereitgestellt)

- ❌ Prometheus Server
- ❌ Grafana
- ❌ Elasticsearch
- ❌ Kibana
- ❌ Filebeat
- ❌ Jaeger (direkt)

### Beibehalten (Microservice-spezifisch)

- ✅ OpenTelemetry Integration
- ✅ Custom Metrics
- ✅ Health Checks
- ✅ Structured Logging
- ✅ Redis (Job-Queue)
- ✅ Celery Worker/Beat

## Troubleshooting

### Logs prüfen

```bash
# API Logs
docker logs file_extractor_api

# Worker Logs
docker logs file_extractor_worker

# Redis Logs
docker logs file_extractor_redis
```

### Health Check

```bash
# Liveness
curl http://localhost:8000/health/live

# Readiness
curl http://localhost:8000/health/ready

# Detaillierte Health-Informationen
curl http://localhost:8000/health
```

### OpenTelemetry Status

```bash
# Metriken prüfen (falls Prometheus verfügbar)
curl http://localhost:9464/metrics

# Traces prüfen (über Jaeger UI)
# http://jaeger:16686
```

## Performance

### Ressourcen-Limits

```yaml
resources:
  limits:
    memory: 2G
    cpu: 2.0
  requests:
    memory: 1G
    cpu: 1.0
```

### Skalierung

- **Horizontal**: Mehrere API-Instanzen
- **Worker**: Mehrere Celery-Worker
- **Redis**: Redis Cluster (für Produktion)

## Security

### Container Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

### Network Security

- Nur notwendige Ports exponieren
- Service-to-Service Kommunikation über internes Netzwerk
- OTLP-Endpoint über HTTPS (Produktion)