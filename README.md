# Universal File Content Extractor API

Eine einheitliche API für die Extraktion von Inhalten aus verschiedenen Dateiformaten, entwickelt mit FastAPI und docling.

## 🚀 Features

- **Unified API**: Einheitliche Schnittstelle für verschiedene Dateiformate
- **Multiple Formats**: Unterstützung für PDF, DOCX, TXT, CSV, JSON, XML und mehr
- **Modular Architecture**: Saubere, wartbare Code-Struktur
- **Comprehensive Documentation**: Vollständige API-Dokumentation mit MkDocs
- **Docker Support**: Einfache Deployment-Optionen
- **Extensible**: Einfache Erweiterung für neue Dateiformate

## 📋 Voraussetzungen

- Python 3.8+
- Docker (optional)
- Poetry (für Dependency Management)

## 🛠️ Installation

### Lokale Installation

```bash
# Repository klonen
git clone <repository-url>
cd universal-file-extractor-api

# Dependencies installieren
poetry install

# Umgebung aktivieren
poetry shell

# API starten
uvicorn app.main:app --reload
```

### Docker Installation

```bash
# Image bauen
docker build -t file-extractor-api .

# Container starten
docker run -p 8000:8000 file-extractor-api
```

## 📖 Verwendung

### API Endpoints

- `POST /extract`: Datei-Inhalt extrahieren
- `GET /formats`: Unterstützte Dateiformate anzeigen
- `GET /health`: API-Status prüfen
- `GET /docs`: Interaktive API-Dokumentation

### Beispiel Request

```bash
curl -X POST "http://localhost:8000/extract" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf"
```

## 📚 Dokumentation

Die vollständige Dokumentation ist verfügbar unter:
- **API Docs**: http://localhost:8000/docs
- **MkDocs**: http://localhost:8000/docs-site

## 🏗️ Projektstruktur

```
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── extract.py
│   │   │   └── health.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── pdf_extractor.py
│   │   ├── docx_extractor.py
│   │   └── text_extractor.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── main.py
├── docs/
│   ├── index.md
│   ├── api.md
│   └── deployment.md
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_extractors.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── mkdocs.yml
```

## 🧪 Tests

```bash
# Tests ausführen
pytest

# Mit Coverage
pytest --cov=app
```

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📞 Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im Repository.