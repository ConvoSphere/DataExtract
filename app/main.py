"""
Haupt-Anwendung für die Universal File Extractor API.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import FileExtractorException, convert_to_http_exception


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware für Request-Logging."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Request verarbeiten
        response = await call_next(request)

        # Verarbeitungszeit berechnen
        process_time = time.time() - start_time

        # Response-Header für Verarbeitungszeit hinzufügen
        response.headers['X-Process-Time'] = str(process_time)

        # Logging (in Produktion durch echtes Logging ersetzen)
        if settings.debug:
            print(f'{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s')

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle-Management für die FastAPI-Anwendung."""
    # Startup
    print(f'🚀 Starte {settings.app_name} v{settings.app_version}')
    print(f'📁 Unterstützte Formate: {len(settings.allowed_extensions)}')
    print(f'⚙️  Debug-Modus: {settings.debug}')

    yield

    # Shutdown
    print('🛑 Beende Anwendung...')


# FastAPI-Anwendung erstellen
app = FastAPI(
    title=settings.app_name,
    description="""
    Eine einheitliche API für die Extraktion von Inhalten aus verschiedenen Dateiformaten.
    
    ## Features
    
    * **Unified API**: Einheitliche Schnittstelle für verschiedene Dateiformate
    * **Multiple Formats**: Unterstützung für PDF, DOCX, TXT, CSV, JSON, XML und mehr
    * **Modular Architecture**: Saubere, wartbare Code-Struktur
    * **Comprehensive Documentation**: Vollständige API-Dokumentation
    
    ## Unterstützte Formate
    
    * **PDF**: Text und Metadaten aus PDF-Dateien
    * **DOCX**: Text, Metadaten und Struktur aus Word-Dokumenten
    * **TXT**: Einfache Textdateien
    * **CSV**: Tabellarische Daten
    * **JSON**: Strukturierte JSON-Daten
    * **XML/HTML**: XML-Dokumente und HTML-Seiten
    
    ## Verwendung
    
    1. Laden Sie eine Datei über den `/extract` Endpoint hoch
    2. Die API erkennt automatisch das Dateiformat
    3. Sie erhalten extrahierten Text, Metadaten und strukturierte Daten zurück
    """,
    version=settings.app_version,
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
    lifespan=lifespan,
)

# Middleware hinzufügen
app.add_middleware(RequestLoggingMiddleware)

# CORS-Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Trusted Host Middleware (für Produktion)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=['*'],  # In Produktion spezifische Hosts angeben
    )

# Exception Handler für FileExtractorException
@app.exception_handler(FileExtractorException)
async def file_extractor_exception_handler(request: Request, exc: FileExtractorException):
    """Exception Handler für FileExtractorException."""
    http_exception = convert_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exception.status_code,
        content=http_exception.detail,
    )

# Exception Handler für allgemeine Exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Exception Handler für allgemeine Exceptions."""
    if settings.debug:
        # Im Debug-Modus detaillierte Fehlerinformationen
        return JSONResponse(
            status_code=500,
            content={
                'error': 'INTERNAL_SERVER_ERROR',
                'message': str(exc),
                'details': {
                    'type': type(exc).__name__,
                    'traceback': str(exc),
                },
            },
        )
    # In Produktion generische Fehlermeldung
    return JSONResponse(
        status_code=500,
        content={
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'Ein interner Server-Fehler ist aufgetreten.',
        },
    )

# API-Routen registrieren
app.include_router(api_router, prefix='/api/v1')


@app.get('/', summary='API-Informationen', description='Gibt grundlegende Informationen über die API zurück.')
async def root():
    """Root-Endpoint mit API-Informationen."""
    return {
        'name': settings.app_name,
        'version': settings.app_version,
        'description': 'Eine einheitliche API für die Extraktion von Inhalten aus verschiedenen Dateiformaten',
        'documentation': '/docs',
        'health_check': '/api/v1/health',
        'supported_formats': '/api/v1/formats',
    }


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """Favicon-Endpoint (wird von Browsern automatisch aufgerufen)."""
    raise HTTPException(status_code=404, detail='Favicon nicht verfügbar')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'app.main:app',
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
