"""
Queue-Verwaltung für asynchrone Verarbeitung.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import redis
    from celery import Celery
    from celery.result import AsyncResult
    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False

from app.core.config import settings
from app.models.schemas import AsyncExtractionResponse, JobStatus


class JobQueue:
    """Verwaltung für asynchrone Job-Verarbeitung."""

    def __init__(self):
        if not QUEUE_AVAILABLE:
            raise ImportError('Redis und Celery sind nicht installiert.')

        # Redis-Verbindung
        self.redis_client = redis.from_url(settings.redis_url, db=settings.redis_db)

        # Celery-App
        self.celery_app = Celery(
            'file_extractor',
            broker=settings.redis_url,
            backend=settings.redis_url,
        )

        # Celery-Konfiguration
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=settings.extract_timeout,
            task_soft_time_limit=settings.extract_timeout - 60,
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=1000,
        )

    def submit_job(
        self,
        file_path: Path,
        include_metadata: bool = True,
        include_text: bool = True,
        include_structure: bool = False,
        include_images: bool = False,
        include_media: bool = False,
        callback_url: str | None = None,
        priority: str = 'normal',
    ) -> AsyncExtractionResponse:
        """Übermittelt einen Job zur asynchronen Verarbeitung."""

        job_id = str(uuid.uuid4())

        # Job-Daten erstellen
        job_data = {
            'job_id': job_id,
            'file_path': str(file_path),
            'include_metadata': include_metadata,
            'include_text': include_text,
            'include_structure': include_structure,
            'include_images': include_images,
            'include_media': include_media,
            'callback_url': callback_url,
            'priority': priority,
            'created_at': datetime.now().isoformat(),
            'status': 'queued',
        }

        # Job in Redis speichern
        self.redis_client.hset(
            f'job:{job_id}',
            mapping=job_data,
        )

        # TTL setzen (Aufbewahrung)
        retention_seconds = settings.extract_timeout + 3600  # 1 Stunde extra
        self.redis_client.expire(f'job:{job_id}', retention_seconds)

        # Celery-Task starten
        task = self.celery_app.send_task(
            'app.workers.extract_file',
            args=[job_id],
            priority=self._get_priority_value(priority),
        )

        # Task-ID speichern
        self.redis_client.hset(f'job:{job_id}', 'task_id', task.id)

        return AsyncExtractionResponse(
            job_id=job_id,
            status='queued',
            estimated_completion=self._estimate_completion_time(priority),
        )

    def get_job_status(self, job_id: str) -> JobStatus | None:
        """Gibt den Status eines Jobs zurück."""

        job_data = self.redis_client.hgetall(f'job:{job_id}')
        if not job_data:
            return None

        # Bytes zu Strings konvertieren
        job_data = {k.decode(): v.decode() for k, v in job_data.items()}

        # Status aus Celery abrufen
        task_id = job_data.get('task_id')
        celery_status = 'PENDING'
        progress = 0.0
        result = None
        error = None

        if task_id:
            async_result = AsyncResult(task_id, app=self.celery_app)
            celery_status = async_result.status

            if celery_status == 'SUCCESS':
                progress = 100.0
                try:
                    result_data = async_result.result
                    if isinstance(result_data, dict):
                        result = result_data
                except Exception as e:
                    error = str(e)
            elif celery_status == 'FAILURE':
                error = str(async_result.info)
            elif celery_status == 'PROGRESS':
                progress = async_result.result.get('progress', 0.0)

        # Status-Mapping
        status_mapping = {
            'PENDING': 'queued',
            'STARTED': 'processing',
            'PROGRESS': 'processing',
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'RETRY': 'processing',
            'REVOKED': 'cancelled',
        }

        status = status_mapping.get(celery_status, 'unknown')

        # Zeitstempel
        created_at = datetime.fromisoformat(job_data.get('created_at', datetime.now().isoformat()))
        started_at = None
        completed_at = None

        if celery_status in ['STARTED', 'PROGRESS', 'SUCCESS', 'FAILURE']:
            started_at = created_at + timedelta(seconds=5)  # Geschätzt

        if celery_status in ['SUCCESS', 'FAILURE']:
            completed_at = datetime.now()

        return JobStatus(
            job_id=job_id,
            status=status,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            progress=progress,
            result=result,
            error=error,
        )

    def cancel_job(self, job_id: str) -> bool:
        """Bricht einen Job ab."""

        job_data = self.redis_client.hgetall(f'job:{job_id}')
        if not job_data:
            return False

        job_data = {k.decode(): v.decode() for k, v in job_data.items()}
        task_id = job_data.get('task_id')

        if task_id:
            async_result = AsyncResult(task_id, app=self.celery_app)
            async_result.revoke(terminate=True)

        # Status aktualisieren
        self.redis_client.hset(f'job:{job_id}', 'status', 'cancelled')

        return True

    def get_queue_stats(self) -> dict[str, Any]:
        """Gibt Statistiken über die Warteschlange zurück."""

        # Aktive Jobs zählen
        active_jobs = 0
        queued_jobs = 0
        completed_jobs = 0
        failed_jobs = 0

        for key in self.redis_client.scan_iter('job:*'):
            job_data = self.redis_client.hgetall(key)
            if job_data:
                status = job_data.get(b'status', b'unknown').decode()
                if status == 'queued':
                    queued_jobs += 1
                elif status == 'processing':
                    active_jobs += 1
                elif status == 'completed':
                    completed_jobs += 1
                elif status == 'failed':
                    failed_jobs += 1

        return {
            'active_jobs': active_jobs,
            'queued_jobs': queued_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'total_jobs': active_jobs + queued_jobs + completed_jobs + failed_jobs,
            'queue_size': settings.queue_size,
        }

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Bereinigt alte Jobs."""

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0

        for key in self.redis_client.scan_iter('job:*'):
            job_data = self.redis_client.hgetall(key)
            if job_data:
                created_at_str = job_data.get(b'created_at')
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.decode())
                        if created_at < cutoff_time:
                            self.redis_client.delete(key)
                            deleted_count += 1
                    except ValueError:
                        pass

        return deleted_count

    def _get_priority_value(self, priority: str) -> int:
        """Konvertiert Priorität in Celery-Prioritätswert."""
        priority_mapping = {
            'low': 10,
            'normal': 5,
            'high': 1,
        }
        return priority_mapping.get(priority, 5)

    def _estimate_completion_time(self, priority: str) -> datetime | None:
        """Schätzt die Fertigstellungszeit."""
        # Einfache Schätzung basierend auf Priorität
        base_time = datetime.now()

        if priority == 'high':
            estimated = base_time + timedelta(minutes=5)
        elif priority == 'normal':
            estimated = base_time + timedelta(minutes=15)
        else:  # low
            estimated = base_time + timedelta(minutes=30)

        return estimated


# Globale Queue-Instanz
job_queue: JobQueue | None = None


def get_job_queue() -> JobQueue:
    """Gibt die globale Job-Queue-Instanz zurück."""
    global job_queue
    if job_queue is None:
        if QUEUE_AVAILABLE:
            job_queue = JobQueue()
        else:
            raise ImportError('Queue-System nicht verfügbar')
    return job_queue
