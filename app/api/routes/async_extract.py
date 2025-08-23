"""
API-Routen für asynchrone Datei-Extraktion.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.auth import check_rate_limit, get_current_user
from app.core.config import settings
from app.core.exceptions import FileExtractorException, convert_to_http_exception
from app.core.queue import get_job_queue
from app.core.validation import validate_file_upload
from app.extractors import is_format_supported
from app.models.schemas import (
    AsyncExtractionResponse,
    ErrorResponse,
    JobStatus,
)

router = APIRouter()


@router.post(
    '/extract/async',
    response_model=AsyncExtractionResponse,
    responses={
        400: {'model': ErrorResponse},
        413: {'model': ErrorResponse},
        415: {'model': ErrorResponse},
        500: {'model': ErrorResponse},
    },
    summary='Asynchrone Datei-Extraktion',
    description='Startet eine asynchrone Extraktion und gibt eine Job-ID zurück.',
)
async def extract_file_async(
    file: UploadFile = File(..., description='Zu extrahierende Datei'),
    include_metadata: bool = Form(True, description='Metadaten extrahieren'),
    include_text: bool = Form(True, description='Text extrahieren'),
    include_structure: bool = Form(
        False,
        description='Strukturierte Daten extrahieren',
    ),
    include_images: bool = Form(False, description='Bilder extrahieren'),
    include_media: bool = Form(False, description='Medien extrahieren'),
    callback_url: str | None = Form(
        None,
        description='Callback-URL für Benachrichtigungen',
    ),
    priority: str = Form('normal', description='Priorität (low, normal, high)'),
    _user: dict = Depends(get_current_user),
    _: dict = Depends(check_rate_limit),
    file_info: dict = Depends(validate_file_upload),
) -> AsyncExtractionResponse:
    """
    Startet eine asynchrone Extraktion einer Datei.

    Args:
        file: Die zu extrahierende Datei
        include_metadata: Ob Metadaten extrahiert werden sollen
        include_text: Ob Text extrahiert werden soll
        include_structure: Ob strukturierte Daten extrahiert werden sollen
        include_images: Ob Bilder extrahiert werden sollen
        include_media: Ob Medien extrahiert werden sollen
        callback_url: URL für Benachrichtigungen bei Fertigstellung
        priority: Priorität der Verarbeitung

    Returns:
        AsyncExtractionResponse mit Job-ID und Status
    """
    try:
        # Temporäre Datei aus Validierung verwenden
        temp_file_path = Path(file_info['temp_path'])

        # Datei-Format prüfen (Extractor-Fähigkeit)
        if not is_format_supported(temp_file_path):
            raise HTTPException(
                status_code=415,
                detail=f"Dateiformat '{Path(file.filename).suffix}' wird nicht unterstützt",
            )

        # Job-Queue abrufen
        queue = get_job_queue()

        # Job zur asynchronen Verarbeitung übermitteln
        return queue.submit_job(
            file_path=temp_file_path,
            include_metadata=include_metadata,
            include_text=include_text,
            include_structure=include_structure,
            include_images=include_images,
            include_media=include_media,
            callback_url=callback_url,
            priority=priority,
        )

    except HTTPException:
        # Temporäre Datei bei Fehler löschen
        Path(file_info.get('temp_path', '')).unlink(missing_ok=True)
        raise
    except FileExtractorException as e:
        Path(file_info.get('temp_path', '')).unlink(missing_ok=True)
        raise convert_to_http_exception(e) from e
    except Exception as e:
        Path(file_info.get('temp_path', '')).unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f'Unerwarteter Fehler: {e!s}',
        ) from e


@router.get(
    '/jobs/{job_id}',
    response_model=JobStatus,
    responses={
        404: {'model': ErrorResponse},
        500: {'model': ErrorResponse},
    },
    summary='Job-Status abfragen',
    description='Gibt den aktuellen Status eines asynchronen Jobs zurück.',
)
async def get_job_status(job_id: str) -> JobStatus:
    """
    Gibt den Status eines asynchronen Jobs zurück.

    Args:
        job_id: ID des Jobs

    Returns:
        JobStatus mit aktuellen Informationen
    """
    try:
        queue = get_job_queue()
        job_status = queue.get_job_status(job_id)

        if not job_status:
            raise HTTPException(
                status_code=404,
                detail=f'Job {job_id} nicht gefunden',
            )

        return job_status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Fehler beim Abrufen des Job-Status: {e!s}',
        ) from e


@router.delete(
    '/jobs/{job_id}',
    summary='Job abbrechen',
    description='Bricht einen asynchronen Job ab.',
)
async def cancel_job(job_id: str):
    """
    Bricht einen asynchronen Job ab.

    Args:
        job_id: ID des Jobs

    Returns:
        Erfolgsmeldung
    """
    try:
        queue = get_job_queue()
        success = queue.cancel_job(job_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f'Job {job_id} nicht gefunden oder bereits abgeschlossen',
            )

        return {'message': f'Job {job_id} wurde abgebrochen'}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Fehler beim Abbrechen des Jobs: {e!s}',
        ) from e


@router.get(
    '/jobs',
    summary='Job-Statistiken',
    description='Gibt Statistiken über alle Jobs zurück.',
)
async def get_job_stats():
    """
    Gibt Statistiken über alle Jobs zurück.

    Returns:
        Job-Statistiken
    """
    try:
        queue = get_job_queue()
        stats = queue.get_queue_stats()

        return {
            'queue_stats': stats,
            'queue_config': {
                'max_concurrent_extractions': settings.max_concurrent_extractions,
                'worker_processes': settings.worker_processes,
                'queue_size': settings.queue_size,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Fehler beim Abrufen der Job-Statistiken: {e!s}',
        ) from e


@router.post(
    '/jobs/cleanup',
    summary='Alte Jobs bereinigen',
    description='Bereinigt alte, abgeschlossene Jobs.',
)
async def cleanup_old_jobs(max_age_hours: int = 24):
    """
    Bereinigt alte, abgeschlossene Jobs.

    Args:
        max_age_hours: Maximales Alter der Jobs in Stunden

    Returns:
        Anzahl gelöschter Jobs
    """
    try:
        queue = get_job_queue()
        deleted_count = queue.cleanup_old_jobs(max_age_hours)

        return {
            'message': f'{deleted_count} alte Jobs wurden bereinigt',
            'deleted_count': deleted_count,
            'max_age_hours': max_age_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Fehler bei der Job-Bereinigung: {e!s}',
        ) from e
