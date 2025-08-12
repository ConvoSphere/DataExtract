"""
Haupt-Anwendung für die Universal File Extractor API.
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import FileExtractorException, convert_to_http_exception
from app.core.logging import (
    get_logger,
    get_tracer,
    log_request_info,
    setup_custom_metrics,
    setup_opentelemetry,
    setup_structured_logging,
)
from app.core.metrics import MetricsCollector, set_metrics_collector
from app.core.security import get_security_middleware

# Global metrics instance
metrics = None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware für strukturiertes Request-Logging."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger('request_middleware')
        self.tracer = get_tracer('request_middleware')

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Span für Request erstellen
        with self.tracer.start_as_current_span('http_request') as span:
            span.set_attribute('http.method', request.method)
            span.set_attribute('http.url', str(request.url))
            span.set_attribute('http.user_agent', request.headers.get('user-agent', ''))
            span.set_attribute(
                'http.client_ip', request.client.host if request.client else '',
            )

            # Request verarbeiten
            response = await call_next(request)

            # Verarbeitungszeit berechnen
            process_time = time.time() - start_time

            # Span-Attribute setzen
            span.set_attribute('http.status_code', response.status_code)
            span.set_attribute('http.duration', process_time)

            # Response-Header für Verarbeitungszeit hinzufügen
            response.headers['X-Process-Time'] = str(process_time)

            # Strukturiertes Logging
            if settings.enable_request_logging:
                log_request_info(
                    self.logger,
                    {
                        'method': request.method,
                        'url': str(request.url),
                        'status_code': response.status_code,
                        'duration': process_time,
                        'user_agent': request.headers.get('user-agent'),
                        'client_ip': request.client.host if request.client else None,
                    },
                )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle-Management für die FastAPI-Anwendung."""
    # Startup
    logger = get_logger('startup')
    tracer = get_tracer('startup')

    with tracer.start_as_current_span('application_startup') as span:
        # Logging und OpenTelemetry initialisieren
        setup_structured_logging()

        if settings.enable_opentelemetry:
            setup_opentelemetry()

            # Custom Metrics initialisieren
            global metrics
            metrics = setup_custom_metrics()

            # Metrics Collector initialisieren
            if metrics:
                metrics_collector = MetricsCollector(metrics)
                set_metrics_collector(metrics_collector)

        span.set_attribute('app.name', settings.app_name)
        span.set_attribute('app.version', settings.app_version)
        span.set_attribute('app.environment', settings.environment)

        logger.info(
            'Application starting',
            app_name=settings.app_name,
            version=settings.app_version,
            supported_formats_count=len(settings.allowed_extensions),
            debug_mode=settings.debug,
            environment=settings.environment,
            otlp_enabled=settings.enable_opentelemetry,
            otlp_endpoint=settings.otlp_endpoint,
        )

    yield

    # Graceful Shutdown
    logger.info('Application shutting down - starting graceful shutdown')

    try:
        # 1. Health Check auf "unhealthy" setzen
        logger.info('Setting health status to unhealthy')

        # 2. Neue Requests ablehnen
        logger.info('Rejecting new requests')

        # 3. In-flight Requests warten lassen
        logger.info('Waiting for in-flight requests to complete')

        # 4. OpenTelemetry Exporters schließen
        if settings.enable_opentelemetry:
            logger.info('Closing OpenTelemetry exporters')
            try:
                from opentelemetry import trace

                trace.get_tracer_provider().shutdown()
            except Exception as e:
                logger.warning(f'Error shutting down OpenTelemetry: {e}')

        # 5. Redis-Verbindungen schließen
        logger.info('Closing Redis connections')
        try:
            from app.core.queue import get_job_queue

            queue = get_job_queue()
            if hasattr(queue, 'redis_client'):
                queue.redis_client.close()
        except Exception as e:
            logger.warning(f'Error closing Redis connections: {e}')

        # 6. Temporäre Dateien bereinigen
        logger.info('Cleaning up temporary files')
        try:
            import shutil
            import tempfile

            temp_dir = Path(tempfile.gettempdir()) / 'file_extractor'
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f'Error cleaning up temp files: {e}')

        logger.info('Graceful shutdown completed')

    except Exception as e:
        logger.error(f'Error during graceful shutdown: {e}')

    logger.info('Application shutdown complete')


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
    * **OpenTelemetry Integration**: Distributed Tracing und Metriken

    ## Unterstützte Formate

    * **Dokumente**: PDF, DOCX, TXT, RTF, ODT, DOC
    * **Tabellen**: XLSX, XLS, ODS, CSV
    * **Präsentationen**: PPTX, PPT, ODP
    * **Datenformate**: JSON, XML, HTML, YAML
    * **Bilder**: JPG, PNG, GIF, BMP, TIFF, WebP, SVG
    * **Medien**: MP4, AVI, MOV, MP3, WAV, FLAC
    * **Archive**: ZIP, RAR, 7Z, TAR, GZ

    ## Microservice Features

    * **Health Checks**: `/health/live`, `/health/ready`
    * **OpenTelemetry**: Distributed Tracing und Metriken
    * **Structured Logging**: JSON-basiertes Logging
    * **Async Processing**: Celery-basierte asynchrone Verarbeitung
    """,
    version=settings.app_version,
    docs_url='/docs' if settings.debug else None,
    redoc_url='/redoc' if settings.debug else None,
    openapi_url='/openapi.json' if settings.debug else None,
    lifespan=lifespan,
)

# OpenTelemetry Instrumentation (muss vor anderen Middlewares hinzugefügt werden)
if settings.enable_opentelemetry:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        print(f'Warning: OpenTelemetry instrumentation failed: {e}')

# Security Middleware hinzufügen
for middleware_class in get_security_middleware():
    app.add_middleware(middleware_class)

# Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS-Middleware (sicher konfiguriert)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Trusted Host Middleware (für Produktion)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            h.strip() for h in settings.allowed_hosts.split(',') if h.strip()
        ],
    )


# Exception Handler für FileExtractorException
@app.exception_handler(FileExtractorException)
async def file_extractor_exception_handler(
    request: Request, exc: FileExtractorException,
):
    """Exception Handler für FileExtractorException."""
    http_exception = convert_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exception.status_code,
        content=http_exception.detail,
    )


# Exception Handler für Validierungsfehler
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError,
):
    content_type = request.headers.get('content-type', '')
    path = str(request.url.path)
    if path.endswith('/api/v1/extract') and content_type.startswith(
        'multipart/form-data',
    ):
        return JSONResponse(
            status_code=400,
            content={
                'error': 'BAD_REQUEST',
                'message': 'Ungültiger Datei-Upload',
            },
        )
    return JSONResponse(
        status_code=422,
        content={'detail': 'Validation error'},
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


@app.get(
    '/',
    summary='API-Informationen',
    description='Gibt grundlegende Informationen über die API zurück.',
)
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
