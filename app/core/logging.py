"""
Strukturiertes Logging und OpenTelemetry-Konfiguration für Microservice.
"""

import logging
import sys
from datetime import datetime
from typing import Any

import structlog
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings


def setup_structured_logging() -> None:
    """Konfiguriert strukturiertes Logging mit structlog."""

    # Structlog-Konfiguration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if not settings.debug
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Standard-Logging konfigurieren
    logging.basicConfig(
        format='%(message)s',
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def setup_opentelemetry() -> None:
    """Konfiguriert OpenTelemetry für Tracing und Metriken."""

    # Resource für Service-Informationen
    resource = Resource.create(
        {
            'service.name': settings.app_name,
            'service.version': settings.app_version,
            'service.instance.id': f'{settings.app_name}-{datetime.now().isoformat()}',
            'deployment.environment': settings.environment,
            'service.namespace': 'file-extractor',
        },
    )

    # Tracer Provider konfigurieren
    tracer_provider = TracerProvider(resource=resource)

    # Span Exporters konfigurieren
    if settings.debug:
        # Console Exporter für Entwicklung
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    else:
        # OTLP Exporter für Produktion (zentrale Infrastruktur)
        if settings.otlp_endpoint:
            otlp_trace_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))

    # Tracer Provider setzen
    trace.set_tracer_provider(tracer_provider)

    # Meter Provider konfigurieren
    if settings.enable_metrics:
        metric_readers = []

        # OTLP Metric Reader für zentrale Infrastruktur
        if settings.otlp_endpoint:
            otlp_metric_exporter = OTLPMetricExporter(endpoint=settings.otlp_endpoint)
            otlp_reader = PeriodicExportingMetricReader(
                otlp_metric_exporter,
                export_interval_millis=15000,  # 15 Sekunden
            )
            metric_readers.append(otlp_reader)

        if metric_readers:
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=metric_readers,
            )
            metrics.set_meter_provider(meter_provider)

    # Instrumentierungen aktivieren
    LoggingInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Gibt einen strukturierten Logger zurück."""
    return structlog.get_logger(name)


def get_tracer(name: str = None) -> trace.Tracer:
    """Gibt einen OpenTelemetry Tracer zurück."""
    return trace.get_tracer(name or __name__)


def get_meter(name: str = None) -> metrics.Meter:
    """Gibt einen OpenTelemetry Meter zurück."""
    return metrics.get_meter(name or __name__)


# Custom Metrics definieren
def setup_custom_metrics() -> dict:
    """Definiert Custom Metrics für den Microservice."""
    meter = get_meter('file_extractor')

    metrics_dict = {
        # Counter für Extraktionen
        'extractions_total': meter.create_counter(
            name='file_extractions_total',
            description='Total number of file extractions',
            unit='1',
        ),
        # Counter für Extraktionsfehler
        'extraction_errors_total': meter.create_counter(
            name='extraction_errors_total',
            description='Total number of extraction errors',
            unit='1',
        ),
        # Histogram für Extraktionsdauer
        'extraction_duration_seconds': meter.create_histogram(
            name='extraction_duration_seconds',
            description='Duration of file extractions',
            unit='s',
        ),
        # Gauge für aktive Jobs
        'active_jobs': meter.create_up_down_counter(
            name='active_jobs',
            description='Number of currently active extraction jobs',
            unit='1',
        ),
        # Counter für unterstützte Dateitypen
        'file_type_extractions_total': meter.create_counter(
            name='file_type_extractions_total',
            description='Total extractions by file type',
            unit='1',
        ),
        # Histogram für Dateigrößen
        'file_size_bytes': meter.create_histogram(
            name='file_size_bytes', description='Size of processed files', unit='bytes',
        ),
    }

    return metrics_dict


def log_request_info(
    logger: structlog.stdlib.BoundLogger, request_info: dict[str, Any],
) -> None:
    """Loggt Request-Informationen strukturiert."""
    logger.info(
        'HTTP Request',
        method=request_info.get('method'),
        url=request_info.get('url'),
        status_code=request_info.get('status_code'),
        duration=request_info.get('duration'),
        user_agent=request_info.get('user_agent'),
        client_ip=request_info.get('client_ip'),
    )


def log_extraction_start(
    logger: structlog.stdlib.BoundLogger, file_info: dict[str, Any],
) -> None:
    """Loggt den Start einer Extraktion."""
    logger.info(
        'Extraction started',
        filename=file_info.get('filename'),
        file_size=file_info.get('file_size'),
        file_type=file_info.get('file_type'),
        extractor=file_info.get('extractor'),
    )


def log_extraction_complete(
    logger: structlog.stdlib.BoundLogger, result_info: dict[str, Any],
) -> None:
    """Loggt den Abschluss einer Extraktion."""
    logger.info(
        'Extraction completed',
        filename=result_info.get('filename'),
        success=result_info.get('success'),
        duration=result_info.get('duration'),
        text_length=result_info.get('text_length'),
        word_count=result_info.get('word_count'),
        warnings=result_info.get('warnings'),
        errors=result_info.get('errors'),
    )


def log_extraction_error(
    logger: structlog.stdlib.BoundLogger, error_info: dict[str, Any],
) -> None:
    """Loggt Extraktionsfehler."""
    logger.error(
        'Extraction failed',
        filename=error_info.get('filename'),
        error_type=error_info.get('error_type'),
        error_message=error_info.get('error_message'),
        stack_trace=error_info.get('stack_trace'),
    )


def log_job_status(
    logger: structlog.stdlib.BoundLogger, job_info: dict[str, Any],
) -> None:
    """Loggt Job-Status-Änderungen."""
    logger.info(
        'Job status changed',
        job_id=job_info.get('job_id'),
        status=job_info.get('status'),
        progress=job_info.get('progress'),
        duration=job_info.get('duration'),
    )


# Globale Logger-Instanz
logger = get_logger(__name__)
