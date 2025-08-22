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

# Mit OpenTelemetry Collector
docker-compose -f docker-compose.microservice.yml -f docker-compose.otel.yml up -d
```

### Kubernetes

```bash
# Namespace erstellen
kubectl create namespace file-extractor

# Deployments anwenden
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Status prüfen
kubectl get pods -n file-extractor
kubectl get services -n file-extractor
```

### Environment-Konfiguration

```bash
# Environment-Datei verwenden
cp .env.microservice .env

# Oder Umgebungsvariablen setzen
export OTLP_ENDPOINT=http://otel-collector:4317
export ENABLE_OPENTELEMETRY=true
export SERVICE_NAME=file-extractor
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

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### Service Mesh Integration

Für Service Mesh (z.B. Istio) Integration:

```yaml
# Service Mesh Annotations
annotations:
  sidecar.istio.io/inject: "true"
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/health"
```

## Implementierte Features

### ✅ Vollständig implementiert

1. **OpenTelemetry Integration**
   - Strukturiertes Logging mit Trace-Korrelation
   - Custom Metrics für Business-Logic
   - Distributed Tracing für alle Operationen
   - OTLP Export für zentrale Infrastruktur

2. **Health Checks**
   - Liveness Probe (`/health/live`)
   - Readiness Probe (`/health/ready`)
   - Detaillierte Health-Informationen (`/health`)

3. **Metrics Collection**
   - Extraktions-Counter und -Dauer
   - Fehler-Tracking
   - Job-Status-Monitoring
   - Dateityp-spezifische Metriken

4. **Performance-Optimierung**
   - Asynchrone Verarbeitung
   - Worker-Skalierung
   - Ressourcen-Limits
   - Memory-Management

5. **Security**
   - Container Security Context
   - Read-only Root Filesystem
   - Capability Dropping
   - Non-root User

### 📊 Performance-Metriken

- **Health Check Response Time**: < 100ms
- **Concurrent Requests**: 20+ gleichzeitig
- **Memory Usage**: < 500MB
- **CPU Usage**: < 50% im Leerlauf
- **OpenTelemetry Overhead**: < 10ms

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

# OpenTelemetry Collector Logs
docker logs file_extractor_otel_collector
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
# Collector Health Check
curl http://localhost:13133

# Metriken prüfen (falls Prometheus verfügbar)
curl http://localhost:9464/metrics

# Traces prüfen (über Jaeger UI)
# http://jaeger:16686
```

### Performance-Tests

```bash
# Performance-Tests ausführen
pytest tests/test_performance_microservice.py -v

# Spezifische Tests
pytest tests/test_performance_microservice.py::TestMicroservicePerformance::test_health_endpoint_performance -v
```

## Monitoring Dashboard

### Prometheus Queries

```promql
# Extraktionen pro Minute
rate(file_extractions_total[1m])

# Extraktionsdauer (95. Perzentil)
histogram_quantile(0.95, rate(extraction_duration_seconds_bucket[5m]))

# Aktive Jobs
file_extractor_active_jobs

# Fehlerrate
rate(extraction_errors_total[5m]) / rate(file_extractions_total[5m])
```

### Grafana Alerts

```yaml
# High Error Rate
- alert: HighExtractionErrorRate
  expr: rate(extraction_errors_total[5m]) / rate(file_extractions_total[5m]) > 0.05
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High extraction error rate detected"

# Slow Extractions
- alert: SlowExtractions
  expr: histogram_quantile(0.95, rate(extraction_duration_seconds_bucket[5m])) > 30
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Slow extractions detected"
```

## Nächste Schritte

1. **✅ Infrastructure-Komponenten entfernt**
2. **✅ OpenTelemetry Collector konfiguriert**
3. **✅ Custom Metrics implementiert**
4. **✅ Performance-Tests erstellt**
5. **🔄 Service Mesh Integration (optional)**
6. **🔄 Erweiterte Monitoring-Dashboards**
7. **🔄 Auto-Scaling Policies**
8. **🔄 Chaos Engineering Tests**

## Support

Bei Fragen oder Problemen:

1. **Logs prüfen**: Strukturiertes JSON-Logging mit Trace-IDs
2. **Health Checks**: Endpoints für Liveness und Readiness
3. **Metrics**: OpenTelemetry-basierte Metriken
4. **Performance-Tests**: Automatisierte Tests für Performance
5. **Documentation**: Vollständige API-Dokumentation unter `/docs`
