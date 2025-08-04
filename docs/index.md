# Universal File Extractor API Documentation

Welcome to the Universal File Extractor API documentation. This API provides a unified interface for extracting content from various file formats using advanced AI-powered extraction techniques.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/universal-file-extractor-api
cd universal-file-extractor-api

# Start with Docker (recommended)
docker-compose up -d

# Or install locally
uv sync
uv run uvicorn app.main:app --reload
```

### First Request

```python
import requests

# Extract content from a file
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/extract',
        files={'file': f},
        data={'include_metadata': 'true', 'include_text': 'true'}
    )
    
result = response.json()
print(f"Extracted text: {result['extracted_text']['content'][:200]}...")
```

## Documentation Sections

### 📚 [Installation Guide](installation.md)
Complete setup instructions for different environments:
- Docker deployment options
- Local development setup
- Environment configuration
- Troubleshooting

### 🔌 [API Reference](api.md)
Comprehensive API documentation:
- All endpoints and parameters
- Request/response examples
- Error handling
- Rate limiting
- Code examples in multiple languages

### 🚀 [Deployment Guide](deployment.md)
Production deployment strategies:
- Docker Compose configurations
- Kubernetes deployment
- Cloud platform deployment
- Monitoring and observability
- Security considerations
- Scaling strategies

### 👨‍💻 [Development Guide](development.md)
Guide for contributors and developers:
- Development environment setup
- Code quality tools
- Testing strategies
- Adding new extractors
- Performance optimization
- Contributing guidelines

## Supported File Formats

### Documents
- **PDF** - Text extraction, OCR, metadata
- **DOCX/DOC** - Microsoft Word documents
- **RTF** - Rich Text Format
- **ODT** - OpenDocument Text
- **TXT** - Plain text files

### Spreadsheets
- **XLSX/XLS** - Microsoft Excel
- **ODS** - OpenDocument Spreadsheet
- **CSV** - Comma-separated values

### Presentations
- **PPTX/PPT** - Microsoft PowerPoint
- **ODP** - OpenDocument Presentation

### Data Formats
- **JSON** - JavaScript Object Notation
- **XML** - Extensible Markup Language
- **HTML** - HyperText Markup Language
- **YAML** - YAML Ain't Markup Language

### Images
- **JPG/JPEG, PNG, GIF, BMP, TIFF, WebP, SVG**
- OCR text extraction
- Metadata extraction

### Media
- **MP4, AVI, MOV** - Video files
- **MP3, WAV, FLAC** - Audio files
- Audio transcription (when available)

### Archives
- **ZIP, RAR, 7Z, TAR, GZ**
- Automatic extraction and processing

## Key Features

### 🔄 Asynchronous Processing
- Large file support (up to 150MB)
- Background job processing
- Real-time status updates
- Priority queuing

### 🤖 AI-Powered Extraction
- **Docling integration** for advanced content analysis
- Intelligent text recognition
- Structured data extraction
- Entity recognition
- Sentiment analysis

### 📊 Monitoring & Observability
- Prometheus metrics
- Grafana dashboards
- Distributed tracing with Jaeger
- Structured logging
- Health checks

### 🏗️ Scalable Architecture
- Microservices design
- Redis-based job queue
- Horizontal scaling support
- Load balancing ready

### 🔒 Security & Performance
- Input validation
- Rate limiting
- Secure file handling
- Resource optimization
- Container security

## Architecture Overview

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
│ • Docling       │    │ • Prometheus    │    │ • Temp Files    │
│ • PDF Extractor │    │ • Grafana       │    │ • Results       │
│ • Image Extractor│   │ • Health Checks │    │ • Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Performance Benchmarks

| File Type | Size | Processing Time | Memory Usage |
|-----------|------|-----------------|--------------|
| PDF (Text) | 1MB | 0.5s | 50MB |
| PDF (OCR) | 1MB | 3.0s | 100MB |
| DOCX | 1MB | 1.0s | 30MB |
| Image (OCR) | 5MB | 2.5s | 80MB |
| Video (5min) | 50MB | 30.0s | 200MB |

## Getting Help

### 📖 Documentation
- [Installation Guide](installation.md) - Setup instructions
- [API Reference](api.md) - Complete API documentation
- [Deployment Guide](deployment.md) - Production deployment
- [Development Guide](development.md) - Contributing guide

### 🐛 Issues & Support
- [GitHub Issues](https://github.com/yourusername/universal-file-extractor-api/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/yourusername/universal-file-extractor-api/discussions) - Community support
- [Email Support](mailto:support@yourdomain.com) - Direct support

### 🔗 Quick Links
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Health Check](http://localhost:8000/api/v1/health) - Service status
- [Metrics](http://localhost:8000/metrics) - Prometheus metrics
- [Grafana Dashboard](http://localhost:3000) - Monitoring dashboard

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

**Built with ❤️ using FastAPI, Docling, UV, and Ruff**