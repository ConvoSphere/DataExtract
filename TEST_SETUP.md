# 🧪 Test-Umgebung Setup

Diese Anleitung beschreibt die Einrichtung und Verwendung der erweiterten Test-Umgebung mit strukturiertem Logging und OpenTelemetry-Monitoring.

## 🚀 Schnellstart

### 1. Test-Umgebung starten

```bash
# Vollständige Test-Umgebung mit Monitoring starten
make test-env

# Oder direkt mit Docker Compose
docker-compose -f docker-compose.test.yml up --build -d
```

### 2. Services überprüfen

```bash
# Status aller Services prüfen
docker-compose -f docker-compose.test.yml ps

# Logs anzeigen
make test-env-logs
```

### 3. Zugriff auf Services

| Service | URL | Beschreibung |
|---------|-----|--------------|
| API | http://localhost:8000 | Haupt-API mit Swagger-Docs |
| Jaeger UI | http://localhost:16686 | Distributed Tracing |
| Grafana | http://localhost:3000 | Metriken-Dashboard |
| Prometheus | http://localhost:9090 | Metriken-Sammlung |
| Flower | http://localhost:5555 | Celery-Monitoring |
| Kibana | http://localhost:5601 | Log-Visualisierung |

## 📊 Monitoring & Observability

### Strukturiertes Logging

Die Anwendung verwendet **structlog** für strukturiertes JSON-Logging:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "info",
  "logger": "extractor.pdf_extractor",
  "event": "Extraction started",
  "filename": "document.pdf",
  "file_size": 1024000,
  "include_metadata": true,
  "include_text": true
}
```

### OpenTelemetry Tracing

- **Jaeger**: Distributed Tracing für Request-Flows
- **Prometheus**: Metriken-Sammlung
- **Grafana**: Visualisierung der Metriken

### Log-Aggregation

- **Elasticsearch**: Log-Speicherung
- **Kibana**: Log-Visualisierung
- **Filebeat**: Log-Sammlung

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# Logging
LOG_LEVEL=DEBUG
ENABLE_REQUEST_LOGGING=true
ENABLE_EXTRACTION_LOGGING=true

# OpenTelemetry
ENABLE_OPENTELEMETRY=true
JAEGER_HOST=jaeger
JAEGER_PORT=6831

# Redis
REDIS_URL=redis://redis:6379

# API
DEBUG=true
MAX_FILE_SIZE=157286400
```

### Logging-Konfiguration

```python
# app/core/logging.py
def setup_structured_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        # ...
    )
```

## 🧪 Tests durchführen

### 1. API-Tests

```bash
# API-Health-Check
curl http://localhost:8000/api/v1/health

# Datei hochladen
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@test.pdf" \
  -F "include_metadata=true" \
  -F "include_text=true"
```

### 2. Asynchrone Tests

```bash
# Asynchrone Extraktion starten
curl -X POST http://localhost:8000/api/v1/extract/async \
  -F "file=@large_document.pdf" \
  -F "priority=high"

# Job-Status abfragen
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### 3. Monitoring-Tests

```bash
# Prometheus-Metriken abrufen
curl http://localhost:8000/metrics

# Jaeger-Traces anzeigen
# Öffnen Sie http://localhost:16686 im Browser
```

## 📈 Metriken & Dashboards

### Verfügbare Metriken

- **HTTP-Requests**: Anzahl, Dauer, Status-Codes
- **Extraktionen**: Erfolgsrate, Dauer, Dateitypen
- **System**: CPU, Memory, Disk-Usage
- **Queue**: Job-Status, Warteschlangen-Länge

### Grafana-Dashboards

1. **API-Übersicht**: Request-Rate, Response-Zeiten
2. **Extraktions-Monitoring**: Erfolgsrate, Durchsatz
3. **System-Metriken**: Ressourcen-Nutzung
4. **Error-Tracking**: Fehler-Rate, Fehler-Typen

## 🔍 Troubleshooting

### Häufige Probleme

#### 1. Services starten nicht

```bash
# Logs prüfen
docker-compose -f docker-compose.test.yml logs api

# Services neu starten
make test-env-restart
```

#### 2. OpenTelemetry funktioniert nicht

```bash
# Jaeger-Status prüfen
curl http://localhost:16686/api/services

# Prometheus-Metriken prüfen
curl http://localhost:9090/api/v1/targets
```

#### 3. Logs werden nicht angezeigt

```bash
# Log-Verzeichnis prüfen
ls -la logs/

# Filebeat-Status prüfen
docker-compose -f docker-compose.test.yml logs filebeat
```

### Debug-Modus

```bash
# Debug-Logs aktivieren
export LOG_LEVEL=DEBUG
export DEBUG=true

# Services neu starten
make test-env-restart
```

## 🧹 Aufräumen

### Test-Umgebung stoppen

```bash
# Alle Services stoppen
make test-env-stop

# Volumes löschen (optional)
docker-compose -f docker-compose.test.yml down -v
```

### Logs bereinigen

```bash
# Log-Dateien löschen
rm -rf logs/*

# Docker-Logs bereinigen
docker system prune -f
```

## 📚 Weitere Ressourcen

- [OpenTelemetry Dokumentation](https://opentelemetry.io/docs/)
- [Jaeger Tracing](https://www.jaegertracing.io/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Elasticsearch Stack](https://www.elastic.co/guide/index.html)

## 🆘 Support

Bei Problemen:

1. Logs prüfen: `make test-env-logs`
2. Service-Status: `docker-compose -f docker-compose.test.yml ps`
3. Issue erstellen mit Logs und Konfiguration