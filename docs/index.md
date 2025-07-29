# Universal File Extractor API

Eine einheitliche API für die Extraktion von Inhalten aus verschiedenen Dateiformaten, entwickelt mit FastAPI und modernen Python-Bibliotheken.

## 🚀 Features

### Unterstützte Dateiformate

- **Dokumente**: PDF, DOCX, DOC, RTF, ODT, TXT
- **Tabellen**: XLSX, XLS, ODS, CSV
- **Präsentationen**: PPTX, PPT, ODP
- **Datenformate**: JSON, XML, HTML, YAML
- **Bilder**: JPG, PNG, GIF, BMP, TIFF, WebP, SVG
- **Medien**: MP4, AVI, MOV, MP3, WAV, FLAC
- **Archive**: ZIP, RAR, 7Z, TAR, GZ

### Kernfunktionen

- **Einheitliche API**: Einheitliche Schnittstelle für alle Dateiformate
- **Asynchrone Verarbeitung**: Parallele Verarbeitung großer Dateien
- **OCR-Unterstützung**: Texterkennung in Bildern und PDFs
- **Medien-Extraktion**: Audio/Video-Transkription
- **Strukturierte Daten**: Tabellen, Listen, Überschriften
- **Metadaten**: Umfassende Datei-Informationen
- **Skalierbar**: Cloud-ready mit Docker und Kubernetes

### Technische Highlights

- **150MB Dateigröße**: Unterstützung für große Dateien
- **Parallelisierung**: Bis zu 10 gleichzeitige Extraktionen
- **Verarbeitungspipeline**: Asynchrone Job-Queue mit Redis/Celery
- **Monitoring**: Prometheus/Grafana Integration
- **Container-basiert**: Einfaches Cloud-Deployment

## 🛠️ Schnellstart

### Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/universal-file-extractor-api
cd universal-file-extractor-api

# Mit Docker (empfohlen)
docker-compose up -d

# Oder lokal
poetry install
poetry run uvicorn app.main:app --reload
```

### Erste Schritte

```python
import requests

# Datei hochladen und extrahieren
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/v1/extract', files=files)
    
result = response.json()
print(f"Extrahierter Text: {result['extracted_text']['content'][:200]}...")
```

### Asynchrone Verarbeitung

```python
# Asynchrone Extraktion für große Dateien
response = requests.post(
    'http://localhost:8000/api/v1/extract/async',
    files={'file': open('large_document.pdf', 'rb')},
    data={'priority': 'high'}
)

job_id = response.json()['job_id']

# Status abfragen
status = requests.get(f'http://localhost:8000/api/v1/jobs/{job_id}').json()
print(f"Status: {status['status']}, Fortschritt: {status['progress']}%")
```

## 📊 API-Übersicht

### Haupt-Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/v1/extract` | POST | Synchrone Datei-Extraktion |
| `/api/v1/extract/async` | POST | Asynchrone Datei-Extraktion |
| `/api/v1/jobs/{job_id}` | GET | Job-Status abfragen |
| `/api/v1/formats` | GET | Unterstützte Formate |
| `/api/v1/health` | GET | API-Status |

### Response-Format

```json
{
  "success": true,
  "file_metadata": {
    "filename": "document.pdf",
    "file_size": 1024000,
    "file_type": "application/pdf",
    "page_count": 5
  },
  "extracted_text": {
    "content": "Extrahierter Text...",
    "word_count": 1500,
    "character_count": 8500
  },
  "structured_data": {
    "tables": [...],
    "headings": [...],
    "images": [...]
  },
  "extraction_time": 2.5
}
```

## 🏗️ Architektur

### Komponenten

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │    │   Redis Queue   │
│                 │    │                 │    │                 │
│ • HTTP Server   │◄──►│ • File Processing│◄──►│ • Job Queue     │
│ • API Routes    │    │ • OCR/Media     │    │ • Results Cache │
│ • Validation    │    │ • Parallel Exec │    │ • State Mgmt    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  File Extractors│    │  Monitoring     │    │  Storage        │
│                 │    │                 │    │                 │
│ • PDF Extractor │    │ • Prometheus    │    │ • Temp Files    │
│ • DOCX Extractor│    │ • Grafana       │    │ • Results       │
│ • Image Extractor│   │ • Health Checks │    │ • Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Deployment-Optionen

- **Docker Compose**: Für Entwicklung und kleine Produktionsumgebungen
- **Kubernetes**: Für große, skalierbare Deployments
- **Cloud Services**: AWS, Azure, Google Cloud
- **Serverless**: AWS Lambda, Google Cloud Functions

## 📈 Performance

### Benchmarks

| Dateityp | Größe | Verarbeitungszeit | Speicher |
|----------|-------|-------------------|----------|
| PDF (Text) | 1MB | 0.5s | 50MB |
| PDF (OCR) | 1MB | 3.0s | 100MB |
| DOCX | 1MB | 1.0s | 30MB |
| Bild (OCR) | 5MB | 2.5s | 80MB |
| Video (5min) | 50MB | 30.0s | 200MB |

### Skalierung

- **Parallele Jobs**: Bis zu 10 gleichzeitig
- **Worker-Instanzen**: Horizontale Skalierung
- **Dateigröße**: Bis zu 150MB pro Datei
- **Timeout**: 10 Minuten pro Extraktion

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# API-Konfiguration
DEBUG=false
MAX_FILE_SIZE=157286400  # 150MB
ENABLE_ASYNC_PROCESSING=true

# Redis-Konfiguration
REDIS_URL=redis://localhost:6379

# Worker-Konfiguration
MAX_CONCURRENT_EXTRACTIONS=10
WORKER_PROCESSES=4

# OCR-Konfiguration
EXTRACT_IMAGE_TEXT=true
EXTRACT_AUDIO_TRANSCRIPT=false
```

## 📚 Dokumentation

- **[API-Dokumentation](api/overview.md)**: Vollständige API-Referenz
- **[Entwickler-Guide](development/installation.md)**: Installation und Setup
- **[Extraktoren](extractors/overview.md)**: Details zu allen Extraktoren
- **[Deployment](deployment/docker.md)**: Cloud-Deployment-Anleitung
- **[Beispiele](examples/quickstart.md)**: Code-Beispiele in verschiedenen Sprachen

## 🤝 Beitragen

Wir freuen uns über Beiträge! Bitte lesen Sie unsere [Contributing Guidelines](CONTRIBUTING.md).

### Entwicklung

```bash
# Entwicklungsumgebung einrichten
poetry install --with dev
pre-commit install

# Tests ausführen
pytest

# Code formatieren
black app/
isort app/

# Dokumentation bauen
mkdocs serve
```

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/universal-file-extractor-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/universal-file-extractor-api/discussions)
- **Email**: support@yourdomain.com

---

**Entwickelt mit ❤️ und FastAPI**