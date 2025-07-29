"""
Celery-Tasks für asynchrone Datei-Extraktion.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from celery import current_task

from app.extractors import get_extractor
from app.core.queue import get_job_queue
from app.core.config import settings


def extract_file_task(job_id: str) -> Dict[str, Any]:
    """
    Celery-Task für asynchrone Datei-Extraktion.
    
    Args:
        job_id: ID des Jobs
        
    Returns:
        Extraktionsergebnis
    """
    try:
        # Job-Queue abrufen
        queue = get_job_queue()
        
        # Job-Daten abrufen
        job_data = queue.redis_client.hgetall(f"job:{job_id}")
        if not job_data:
            raise ValueError(f"Job {job_id} nicht gefunden")
        
        # Bytes zu Strings konvertieren
        job_data = {k.decode(): v.decode() for k, v in job_data.items()}
        
        # Status auf "processing" setzen
        queue.redis_client.hset(f"job:{job_id}", "status", "processing")
        
        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 10}
        )
        
        # Dateipfad
        file_path = Path(job_data["file_path"])
        
        # Extraktionsparameter
        include_metadata = job_data.get("include_metadata", "true").lower() == "true"
        include_text = job_data.get("include_text", "true").lower() == "true"
        include_structure = job_data.get("include_structure", "false").lower() == "true"
        include_images = job_data.get("include_images", "false").lower() == "true"
        include_media = job_data.get("include_media", "false").lower() == "true"
        
        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 30}
        )
        
        # Passenden Extraktor finden
        extractor = get_extractor(file_path)
        
        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 50}
        )
        
        # Extraktion durchführen
        result = extractor.extract(
            file_path=file_path,
            include_metadata=include_metadata,
            include_text=include_text,
            include_structure=include_structure
        )
        
        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 90}
        )
        
        # Ergebnis in Redis speichern
        result_dict = result.dict()
        queue.redis_client.hset(
            f"job:{job_id}",
            mapping={
                "status": "completed",
                "result": str(result_dict)  # Vereinfachte Speicherung
            }
        )
        
        # Callback-URL aufrufen (falls angegeben)
        callback_url = job_data.get("callback_url")
        if callback_url:
            try:
                import requests
                requests.post(
                    callback_url,
                    json={
                        "job_id": job_id,
                        "status": "completed",
                        "result": result_dict
                    },
                    timeout=10
                )
            except Exception as e:
                print(f"Callback-Fehler: {e}")
        
        # Fortschritt melden
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 100}
        )
        
        return result_dict
        
    except Exception as e:
        # Fehler in Redis speichern
        try:
            queue = get_job_queue()
            queue.redis_client.hset(
                f"job:{job_id}",
                mapping={
                    "status": "failed",
                    "error": str(e)
                }
            )
            
            # Callback-URL für Fehler aufrufen
            callback_url = job_data.get("callback_url") if 'job_data' in locals() else None
            if callback_url:
                try:
                    import requests
                    requests.post(
                        callback_url,
                        json={
                            "job_id": job_id,
                            "status": "failed",
                            "error": str(e)
                        },
                        timeout=10
                    )
                except Exception:
                    pass
                    
        except Exception:
            pass
        
        raise e


# Task-Registrierung für Celery
extract_file = extract_file_task