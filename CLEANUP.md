# Cleanup Guide - Microservice Architecture

## Zu entfernende Dateien

### Infrastructure-Komponenten (werden zentral bereitgestellt)

```bash
# Prometheus-Konfiguration
rm prometheus.yml

# Filebeat-Konfiguration
rm filebeat.yml

# Grafana-Konfiguration
rm -rf grafana/

# Nginx-Konfiguration (falls nicht benötigt)
rm nginx.conf
```

### Docker Compose Files

```bash
# Alte Docker Compose Files (behalten für Referenz)
# docker-compose.yml (behalten für Development)
# docker-compose.prod.yml (behalten für Referenz)

# Neue Microservice-Version verwenden:
# docker-compose.microservice.yml
```

## Bereinigte Abhängigkeiten

### Entfernt aus pyproject.toml

```toml
# Entfernt:
"prometheus-client>=0.19.0",
"opentelemetry-exporter-prometheus>=1.21.0",
"opentelemetry-exporter-jaeger>=1.21.0",

# Hinzugefügt:
"opentelemetry-instrumentation-redis>=0.42b0",
```

## Neue Architektur

### Beibehaltene Komponenten

- ✅ `app/core/logging.py` (überarbeitet für OpenTelemetry)
- ✅ `app/core/config.py` (überarbeitet für Microservice)
- ✅ `app/core/metrics.py` (neu erstellt)
- ✅ `app/api/routes/health.py` (Health Checks)
- ✅ `app/main.py` (überarbeitet für OpenTelemetry)

### Neue Dateien

- ✅ `docker-compose.microservice.yml` (Microservice-spezifisch)
- ✅ `MICROSERVICE.md` (Dokumentation)
- ✅ `CLEANUP.md` (diese Datei)

## Migration

### 1. Infrastructure-Komponenten entfernen

```bash
# Dateien entfernen
rm prometheus.yml filebeat.yml
rm -rf grafana/

# Docker Compose anpassen
# docker-compose.microservice.yml verwenden
```

### 2. OpenTelemetry konfigurieren

```bash
# Umgebungsvariablen setzen
export OTLP_ENDPOINT=http://otel-collector:4317
export ENABLE_OPENTELEMETRY=true
export ENABLE_METRICS=true
export ENABLE_TRACING=true
```

### 3. Dependencies aktualisieren

```bash
# Neue Dependencies installieren
uv sync

# Alte Dependencies entfernen
uv remove prometheus-client
```

## Vorteile der Bereinigung

### Reduzierte Komplexität

- ❌ Keine lokale Prometheus-Instanz
- ❌ Keine lokale Grafana-Instanz
- ❌ Keine lokale ELK-Stack-Komponenten
- ✅ Fokus auf Business Logic
- ✅ Einfachere Deployment-Pipeline

### Bessere Integration

- ✅ Standardisierte OpenTelemetry-Integration
- ✅ Zentrale Metriken-Sammlung
- ✅ Einheitliches Logging
- ✅ Service Mesh kompatibel

### Ressourcen-Einsparung

- ✅ Weniger Container
- ✅ Weniger Speicherverbrauch
- ✅ Weniger CPU-Verbrauch
- ✅ Einfachere Wartung

## Nächste Schritte

1. **Infrastructure-Komponenten entfernen**
2. **OpenTelemetry Collector konfigurieren**
3. **Zentrale Monitoring-Infrastruktur einrichten**
4. **Service Mesh Integration (optional)**
5. **Performance-Tests durchführen**
