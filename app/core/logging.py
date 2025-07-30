"""
Strukturiertes Logging und OpenTelemetry-Konfiguration.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict

import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

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
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Standard-Logging konfigurieren
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def setup_opentelemetry() -> None:
    """Konfiguriert OpenTelemetry für Tracing und Metriken."""
    
    # Resource für Service-Informationen
    resource = Resource.create({
        "service.name": settings.app_name,
        "service.version": settings.app_version,
        "service.instance.id": f"{settings.app_name}-{datetime.now().isoformat()}",
        "deployment.environment": settings.environment,
    })

    # Tracer Provider konfigurieren
    tracer_provider = TracerProvider(resource=resource)
    
    # Span Exporters konfigurieren
    if settings.debug:
        # Console Exporter für Entwicklung
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    else:
        # Jaeger Exporter für Produktion
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # OTLP Exporter (falls konfiguriert)
        if hasattr(settings, 'otlp_endpoint') and settings.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Tracer Provider setzen
    trace.set_tracer_provider(tracer_provider)

    # Meter Provider konfigurieren
    metric_readers = []
    
    # Prometheus Metric Reader
    prometheus_reader = PrometheusMetricReader()
    metric_readers.append(prometheus_reader)
    
    # OTLP Metric Reader (falls konfiguriert)
    if hasattr(settings, 'otlp_endpoint') and settings.otlp_endpoint:
        otlp_reader = PeriodicExportingMetricReader(
            OTLPSpanExporter(endpoint=settings.otlp_endpoint)
        )
        metric_readers.append(otlp_reader)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=metric_readers,
    )

    # Instrumentierungen aktivieren
    LoggingInstrumentor().instrument()
    RequestsInstrumentor().instrument()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Gibt einen strukturierten Logger zurück."""
    return structlog.get_logger(name)


def log_request_info(logger: structlog.stdlib.BoundLogger, request_info: Dict[str, Any]) -> None:
    """Loggt Request-Informationen strukturiert."""
    logger.info(
        "HTTP Request",
        method=request_info.get("method"),
        url=request_info.get("url"),
        status_code=request_info.get("status_code"),
        duration=request_info.get("duration"),
        user_agent=request_info.get("user_agent"),
        client_ip=request_info.get("client_ip"),
    )


def log_extraction_start(logger: structlog.stdlib.BoundLogger, file_info: Dict[str, Any]) -> None:
    """Loggt den Start einer Extraktion."""
    logger.info(
        "Extraction started",
        filename=file_info.get("filename"),
        file_size=file_info.get("file_size"),
        file_type=file_info.get("file_type"),
        extractor=file_info.get("extractor"),
    )


def log_extraction_complete(logger: structlog.stdlib.BoundLogger, result_info: Dict[str, Any]) -> None:
    """Loggt den Abschluss einer Extraktion."""
    logger.info(
        "Extraction completed",
        filename=result_info.get("filename"),
        success=result_info.get("success"),
        duration=result_info.get("duration"),
        text_length=result_info.get("text_length"),
        word_count=result_info.get("word_count"),
        warnings=result_info.get("warnings"),
        errors=result_info.get("errors"),
    )


def log_extraction_error(logger: structlog.stdlib.BoundLogger, error_info: Dict[str, Any]) -> None:
    """Loggt Extraktionsfehler."""
    logger.error(
        "Extraction failed",
        filename=error_info.get("filename"),
        error_type=error_info.get("error_type"),
        error_message=error_info.get("error_message"),
        stack_trace=error_info.get("stack_trace"),
    )


def log_job_status(logger: structlog.stdlib.BoundLogger, job_info: Dict[str, Any]) -> None:
    """Loggt Job-Status-Änderungen."""
    logger.info(
        "Job status changed",
        job_id=job_info.get("job_id"),
        status=job_info.get("status"),
        progress=job_info.get("progress"),
        duration=job_info.get("duration"),
    )


# Globale Logger-Instanz
logger = get_logger(__name__)