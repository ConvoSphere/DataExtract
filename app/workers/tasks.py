"""
Celery-Tasks für asynchrone Datei-Extraktion.
"""

import time
from pathlib import Path
from typing import Any

from celery import current_task

from app.core.queue import get_job_queue
from app.core.metrics import record_extraction_start, record_extraction_success, record_extraction_error, record_job_status_change
from app.extractors import get_extractor


def extract_file_task(job_id: str) -> dict[str, Any]:
    """
    Celery-Task für asynchrone Datei-Extraktion.

    Args:
        job_id: ID des Jobs

    Returns:
        Extraktionsergebnis
    """
    start_time = time.time()
    
    try:
        # Job-Queue abrufen
        queue = get_job_queue()

        # Job-Daten abrufen
        job_data = queue.redis_client.hgetall(f'job:{job_id}')
        if not job_data:
            raise ValueError(f'Job {job_id} nicht gefunden')

        # Bytes zu Strings konvertieren
        job_data = {k.decode(): v.decode() for k, v in job_data.items()}

        # Status auf "processing" setzen
        queue.redis_client.hset(f'job:{job_id}', 'status', 'processing')
        
        # Job-Status-Änderung aufzeichnen
        record_job_status_change(job_id, "processing")

        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 10},
        )

        # Dateipfad
        file_path = Path(job_data['file_path'])

        # Extraktionsparameter
        include_metadata = job_data.get('include_metadata', 'true').lower() == 'true'
        include_text = job_data.get('include_text', 'true').lower() == 'true'
        include_structure = job_data.get('include_structure', 'false').lower() == 'true'
        include_images = job_data.get('include_images', 'false').lower() == 'true'
        include_media = job_data.get('include_media', 'false').lower() == 'true'

        # Dateigröße ermitteln
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Metrics für Extraktionsstart
        record_extraction_start(
            file_path=file_path,
            file_size=file_size,
            file_type=file_path.suffix.lower()
        )

        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 30},
        )

        # Passenden Extraktor finden
        extractor = get_extractor(file_path)

        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 50},
        )

        # Extraktion durchführen
        result = extractor.extract(
            file_path=file_path,
            include_metadata=include_metadata,
            include_text=include_text,
            include_structure=include_structure,
        )

        # Extraktionsdauer berechnen
        duration = time.time() - start_time

        # Metrics für erfolgreiche Extraktion
        record_extraction_success(
            file_path=file_path,
            duration=duration,
            text_length=len(result.text) if result.text else 0,
            word_count=len(result.text.split()) if result.text else 0
        )

        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 90},
        )

        # Ergebnis in Redis speichern
        result_dict = result.dict()
        queue.redis_client.hset(
            f'job:{job_id}',
            mapping={
                'status': 'completed',
                'result': str(result_dict),  # Vereinfachte Speicherung
            },
        )

        # Job-Status-Änderung aufzeichnen
        record_job_status_change(job_id, "completed", duration)

        # Callback-URL aufrufen (falls angegeben)
        callback_url = job_data.get('callback_url')
        if callback_url:
            try:
                import requests
                requests.post(
                    callback_url,
                    json={
                        'job_id': job_id,
                        'status': 'completed',
                        'result': result_dict,
                    },
                    timeout=10,
                )
            except Exception:
                pass

        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 100},
        )

        return result_dict

    except Exception as e:
        # Extraktionsdauer berechnen
        duration = time.time() - start_time
        
        # Metrics für Extraktionsfehler
        if 'file_path' in locals():
            record_extraction_error(
                file_path=file_path,
                duration=duration,
                error_type=type(e).__name__,
                error_message=str(e)
            )
        
        # Job-Status-Änderung aufzeichnen
        record_job_status_change(job_id, "failed", duration)
        
        # Fehler in Redis speichern
        try:
            queue = get_job_queue()
            queue.redis_client.hset(
                f'job:{job_id}',
                mapping={
                    'status': 'failed',
                    'error': str(e),
                },
            )

            # Callback-URL für Fehler aufrufen
            callback_url = job_data.get('callback_url') if 'job_data' in locals() else None
            if callback_url:
                try:
                    import requests
                    requests.post(
                        callback_url,
                        json={
                            'job_id': job_id,
                            'status': 'failed',
                            'error': str(e),
                        },
                        timeout=10,
                    )
                except Exception:
                    pass

        except Exception:
            pass

        raise e


# Task-Registrierung für Celery
extract_file = extract_file_task
