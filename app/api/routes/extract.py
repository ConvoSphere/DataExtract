"""
API-Routen für die Datei-Extraktion.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.auth import check_rate_limit, get_current_user
from app.core.config import settings
from app.core.exceptions import FileExtractorException, convert_to_http_exception
from app.core.validation import validate_file_upload
import time
from app.core.logging import get_logger
from app.core.metrics import record_extraction_start, record_extraction_success, record_extraction_error
from app.extractors import get_extractor, is_format_supported
from app.models.schemas import ErrorResponse, ExtractionResult

router = APIRouter()
logger = get_logger('extract_routes')


@router.post(
    '/extract',
    response_model=ExtractionResult,
    responses={
        400: {'model': ErrorResponse},
        413: {'model': ErrorResponse},
        415: {'model': ErrorResponse},
        422: {'model': ErrorResponse},
        500: {'model': ErrorResponse},
    },
    summary='Datei-Inhalt extrahieren',
    description='Extrahiert Text, Metadaten und strukturierte Daten aus einer hochgeladenen Datei.',
)
async def extract_file(
    file: UploadFile = File(..., description='Zu extrahierende Datei'),
    include_metadata: bool = Form(True, description='Metadaten extrahieren'),
    include_text: bool = Form(True, description='Text extrahieren'),
    include_structure: bool = Form(False, description='Strukturierte Daten extrahieren'),
    language: str | None = Form(None, description='Sprache für die Extraktion (ISO 639-1)'),
    user: dict = Depends(get_current_user),
    _: dict = Depends(check_rate_limit),
    file_info: dict = Depends(validate_file_upload),
) -> ExtractionResult:
    """
    Extrahiert Inhalt aus einer hochgeladenen Datei.

    Unterstützt verschiedene Dateiformate wie PDF, DOCX, TXT, CSV, JSON, XML und mehr.

    Args:
        file: Die zu extrahierende Datei
        include_metadata: Ob Metadaten extrahiert werden sollen
        include_text: Ob Text extrahiert werden soll
        include_structure: Ob strukturierte Daten extrahiert werden sollen
        language: Sprache für die Extraktion (optional)

    Returns:
        ExtractionResult mit den extrahierten Daten

    Raises:
        400: Ungültige Datei
        413: Datei zu groß
        415: Nicht unterstütztes Format
        422: Extraktion fehlgeschlagen
        500: Server-Fehler
    """
    try:
        start_time = time.time()
        
        # Logging für Extraktionsanfrage
        logger.info(
            'Extraction request received',
            filename=file_info['filename'],
            user=user.get('name'),
            include_metadata=include_metadata,
            include_text=include_text,
            include_structure=include_structure,
            file_hash=file_info['hash'],
        )

        # Datei ist bereits validiert durch validate_file_upload dependency
        # Temporäre Datei aus der Validierung verwenden
        temp_file_path = Path(file_info['temp_path'])

        try:
            # Datei-Format prüfen
            if not is_format_supported(temp_file_path):
                raise HTTPException(
                    status_code=415,
                    detail=f"Dateiformat '{Path(file.filename).suffix}' wird nicht unterstützt",
                )

            # Metrics für Extraktionsstart
            record_extraction_start(
                file_path=temp_file_path,
                file_size=len(content),
                file_type=temp_file_path.suffix.lower()
            )

            # Passenden Extraktor finden
            extractor = get_extractor(temp_file_path)

            # Extraktion durchführen
            result = extractor.extract(
                file_path=temp_file_path,
                include_metadata=include_metadata,
                include_text=include_text,
                include_structure=include_structure,
            )

            # Extraktionsdauer berechnen
            duration = time.time() - start_time

            # Metrics für erfolgreiche Extraktion
            record_extraction_success(
                file_path=temp_file_path,
                duration=duration,
                text_length=len(result.text) if result.text else 0,
                word_count=len(result.text.split()) if result.text else 0
            )

            # Logging für erfolgreiche Extraktion
            logger.info(
                'Extraction completed successfully',
                filename=file.filename,
                file_size=len(content),
                text_length=len(result.text) if result.text else 0,
                word_count=len(result.text.split()) if result.text else 0,
                duration=duration,
            )

            return result


        finally:
            # Temporäre Datei löschen
            try:
                temp_file_path.unlink()
            except Exception:
                pass

    except HTTPException:
        raise
    except FileExtractorException as e:
        # Metrics für Extraktionsfehler
        duration = time.time() - start_time
        record_extraction_error(
            file_path=Path(file.filename) if file.filename else Path("unknown"),
            duration=duration,
            error_type="FileExtractorException",
            error_message=str(e)
        )
        raise convert_to_http_exception(e)
    except Exception as e:
        # Metrics für Extraktionsfehler
        duration = time.time() - start_time
        record_extraction_error(
            file_path=Path(file.filename) if file.filename else Path("unknown"),
            duration=duration,
            error_type="Exception",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f'Unerwarteter Fehler: {e!s}',
        )


@router.get(
    '/formats',
    summary='Unterstützte Formate anzeigen',
    description='Gibt eine Liste aller unterstützten Dateiformate zurück.',
)
async def get_supported_formats():
    """
    Gibt alle unterstützten Dateiformate zurück.

    Returns:
        Liste der unterstützten Formate mit Details
    """
    try:
        formats = get_supported_formats()

        # Formate in das erwartete Schema konvertieren
        supported_formats = []
        for format_info in formats:
            for extension in format_info.get('extensions', []):
                supported_formats.append({
                    'extension': extension,
                    'mime_type': format_info.get('mime_types', [''])[0] if format_info.get('mime_types') else 'application/octet-stream',
                    'description': f"Unterstützt durch {format_info['class']}",
                    'features': ['text_extraction', 'metadata_extraction'],
                    'max_size': format_info.get('max_file_size'),
                })

        return {
            'formats': supported_formats,
            'total_count': len(supported_formats),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Fehler beim Abrufen der Formate: {e!s}',
        )


@router.post(
    '/extract/batch',
    summary='Batch-Extraktion',
    description='Extrahiert Inhalt aus mehreren Dateien gleichzeitig.',
)
async def extract_batch(
    files: list[UploadFile] = File(..., description='Zu extrahierende Dateien'),
    include_metadata: bool = Form(True),
    include_text: bool = Form(True),
    include_structure: bool = Form(False),
):
    """
    Extrahiert Inhalt aus mehreren Dateien in einem Batch.

    Args:
        files: Liste der zu extrahierenden Dateien
        include_metadata: Ob Metadaten extrahiert werden sollen
        include_text: Ob Text extrahiert werden soll
        include_structure: Ob strukturierte Daten extrahiert werden sollen

    Returns:
        Liste der Extraktionsergebnisse
    """
    results = []

    for file in files:
        try:
            # Einzelne Datei extrahieren
            result = await extract_file(
                file=file,
                include_metadata=include_metadata,
                include_text=include_text,
                include_structure=include_structure,
            )
            results.append({
                'filename': file.filename,
                'success': True,
                'result': result,
            })
        except Exception as e:
            results.append({
                'filename': file.filename,
                'success': False,
                'error': str(e),
            })

    return {
        'batch_results': results,
        'total_files': len(files),
        'successful_extractions': len([r for r in results if r['success']]),
        'failed_extractions': len([r for r in results if not r['success']]),
    }
