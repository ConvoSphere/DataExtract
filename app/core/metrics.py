"""
Custom Metrics für den File Extractor Microservice.
"""

import time
from pathlib import Path
from typing import Any, Optional

from app.core.logging import get_logger, get_tracer

logger = get_logger(__name__)
tracer = get_tracer(__name__)


class MetricsCollector:
    """Sammelt und exportiert Custom Metrics für den Microservice."""
    
    def __init__(self, metrics_dict: dict):
        self.metrics = metrics_dict
        self.logger = get_logger('metrics')
    
    def record_extraction_start(self, file_path: Path, file_size: int, file_type: str) -> None:
        """Zeichnet den Start einer Extraktion auf."""
        try:
            # Span für Extraktion erstellen
            with tracer.start_as_current_span("file_extraction") as span:
                span.set_attribute("file.path", str(file_path))
                span.set_attribute("file.size", file_size)
                span.set_attribute("file.type", file_type)
                span.set_attribute("file.extension", file_path.suffix.lower())
                
                # Dateigröße aufzeichnen
                if 'file_size_bytes' in self.metrics:
                    self.metrics['file_size_bytes'].record(file_size)
                
                # Aktive Jobs erhöhen
                if 'active_jobs' in self.metrics:
                    self.metrics['active_jobs'].add(1)
                
                self.logger.info(
                    'Extraction metrics recorded',
                    file_path=str(file_path),
                    file_size=file_size,
                    file_type=file_type,
                )
        except Exception as e:
            self.logger.warning(f'Failed to record extraction start metrics: {e}')
    
    def record_extraction_success(
        self, 
        file_path: Path, 
        duration: float, 
        text_length: int = 0,
        word_count: int = 0
    ) -> None:
        """Zeichnet eine erfolgreiche Extraktion auf."""
        try:
            # Extraktions-Counter erhöhen
            if 'extractions_total' in self.metrics:
                self.metrics['extractions_total'].add(1, {
                    'file_type': file_path.suffix.lower(),
                    'status': 'success'
                })
            
            # Extraktionsdauer aufzeichnen
            if 'extraction_duration_seconds' in self.metrics:
                self.metrics['extraction_duration_seconds'].record(duration, {
                    'file_type': file_path.suffix.lower(),
                    'status': 'success'
                })
            
            # Dateityp-spezifische Metriken
            if 'file_type_extractions_total' in self.metrics:
                self.metrics['file_type_extractions_total'].add(1, {
                    'file_type': file_path.suffix.lower()
                })
            
            # Aktive Jobs verringern
            if 'active_jobs' in self.metrics:
                self.metrics['active_jobs'].add(-1)
            
            self.logger.info(
                'Extraction success metrics recorded',
                file_path=str(file_path),
                duration=duration,
                text_length=text_length,
                word_count=word_count,
            )
        except Exception as e:
            self.logger.warning(f'Failed to record extraction success metrics: {e}')
    
    def record_extraction_error(
        self, 
        file_path: Path, 
        duration: float, 
        error_type: str,
        error_message: str
    ) -> None:
        """Zeichnet einen Extraktionsfehler auf."""
        try:
            # Fehler-Counter erhöhen
            if 'extraction_errors_total' in self.metrics:
                self.metrics['extraction_errors_total'].add(1, {
                    'file_type': file_path.suffix.lower(),
                    'error_type': error_type
                })
            
            # Extraktionsdauer aufzeichnen (auch bei Fehlern)
            if 'extraction_duration_seconds' in self.metrics:
                self.metrics['extraction_duration_seconds'].record(duration, {
                    'file_type': file_path.suffix.lower(),
                    'status': 'error'
                })
            
            # Aktive Jobs verringern
            if 'active_jobs' in self.metrics:
                self.metrics['active_jobs'].add(-1)
            
            self.logger.info(
                'Extraction error metrics recorded',
                file_path=str(file_path),
                duration=duration,
                error_type=error_type,
                error_message=error_message,
            )
        except Exception as e:
            self.logger.warning(f'Failed to record extraction error metrics: {e}')
    
    def record_job_status_change(self, job_id: str, status: str, duration: Optional[float] = None) -> None:
        """Zeichnet Job-Status-Änderungen auf."""
        try:
            with tracer.start_as_current_span("job_status_change") as span:
                span.set_attribute("job.id", job_id)
                span.set_attribute("job.status", status)
                if duration:
                    span.set_attribute("job.duration", duration)
                
                self.logger.info(
                    'Job status change recorded',
                    job_id=job_id,
                    status=status,
                    duration=duration,
                )
        except Exception as e:
            self.logger.warning(f'Failed to record job status change: {e}')


# Global metrics collector instance
metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Gibt die globale Metrics Collector Instanz zurück."""
    return metrics_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """Setzt die globale Metrics Collector Instanz."""
    global metrics_collector
    metrics_collector = collector


def record_extraction_start(file_path: Path, file_size: int, file_type: str) -> None:
    """Hilfsfunktion zum Aufzeichnen des Extraktionsstarts."""
    collector = get_metrics_collector()
    if collector:
        collector.record_extraction_start(file_path, file_size, file_type)


def record_extraction_success(
    file_path: Path, 
    duration: float, 
    text_length: int = 0,
    word_count: int = 0
) -> None:
    """Hilfsfunktion zum Aufzeichnen einer erfolgreichen Extraktion."""
    collector = get_metrics_collector()
    if collector:
        collector.record_extraction_success(file_path, duration, text_length, word_count)


def record_extraction_error(
    file_path: Path, 
    duration: float, 
    error_type: str,
    error_message: str
) -> None:
    """Hilfsfunktion zum Aufzeichnen eines Extraktionsfehlers."""
    collector = get_metrics_collector()
    if collector:
        collector.record_extraction_error(file_path, duration, error_type, error_message)


def record_job_status_change(job_id: str, status: str, duration: Optional[float] = None) -> None:
    """Hilfsfunktion zum Aufzeichnen von Job-Status-Änderungen."""
    collector = get_metrics_collector()
    if collector:
        collector.record_job_status_change(job_id, status, duration)