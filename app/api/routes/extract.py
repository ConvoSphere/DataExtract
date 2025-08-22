"""
API-Routen für die Datei-Extraktion.
"""

import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.auth import check_rate_limit, get_current_user
from app.core.exceptions import FileExtractorException, convert_to_http_exception
from app.core.logging import get_logger
from app.core.metrics import (
    record_extraction_error,
    record_extraction_start,
    record_extraction_success,
    record_tika_fallback,
)
from app.core.validation import validate_file_upload
from app.extractors import (
    get_extractor,
    is_format_supported,
)
from app.extractors import (
    get_supported_formats as list_supported_formats,
)
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
    include_structure: bool = Form(
        False,
        description='Strukturierte Daten extrahieren',
    ),
    language: str | None = Form(
        None,
        description='Sprache für die Extraktion (ISO 639-1)',
    ),
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
                file_size=file_info['size'],
                file_type=temp_file_path.suffix.lower(),
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

            # Optionale Qualitäts-Eskalation zu Tika: Wenn Ergebnis schwach ist
            try:
                from app.core.config import settings as _settings

                if _settings.enable_tika and include_text:
                    text_len = (
                        len(result.extracted_text.content)
                        if result.extracted_text and result.extracted_text.content
                        else 0
                    )
                    # einfache Heuristik: sehr kurzer/leerer Text -> Tika-Fallback
                    if text_len < 20:
                        from app.extractors.tika_extractor import TikaExtractor

                        # Vermeide teure/fehlerhafte Fallbacks wenn Tika nicht verfügbar ist
                        if not TikaExtractor.is_available():
                            raise RuntimeError(
                                'Tika server not available, skipping fallback',
                            )
                        # Metrik erhöhen
                        try:
                            record_tika_fallback()
                        except Exception:
                            pass
                        tika = TikaExtractor()
                        fallback_result = tika.extract(
                            file_path=temp_file_path,
                            include_metadata=include_metadata,
                            include_text=True,
                            include_structure=False,
                        )
                        # Wenn Tika mehr Inhalt liefert, ersetze Text/Metadaten
                        fallback_len = (
                            len(fallback_result.extracted_text.content)
                            if fallback_result.extracted_text
                            and fallback_result.extracted_text.content
                            else 0
                        )
                        if fallback_len > text_len:
                            result.extracted_text = fallback_result.extracted_text
                            if include_metadata and fallback_result.file_metadata:
                                result.file_metadata = fallback_result.file_metadata
            except Exception:
                # Eskalation darf nie die Haupt-Extraktion brechen
                pass

            # Originaler Dateiname in den Metadaten beibehalten
            try:
                if result.file_metadata and file and file.filename:
                    result.file_metadata.filename = file.filename
            except Exception:
                pass

            # Extraktionsdauer berechnen
            duration = time.time() - start_time

            # Metrics für erfolgreiche Extraktion
            record_extraction_success(
                file_path=temp_file_path,
                duration=duration,
                text_length=len(result.extracted_text.content)
                if result.extracted_text and result.extracted_text.content
                else 0,
                word_count=result.extracted_text.word_count
                if result.extracted_text
                and result.extracted_text.word_count is not None
                else 0,
            )

            # Logging für erfolgreiche Extraktion
            logger.info(
                'Extraction completed successfully',
                filename=file.filename,
                file_size=file_info['size'],
                text_length=len(result.extracted_text.content)
                if result.extracted_text and result.extracted_text.content
                else 0,
                word_count=result.extracted_text.word_count
                if result.extracted_text
                and result.extracted_text.word_count is not None
                else 0,
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
            file_path=Path(file.filename) if file.filename else Path('unknown'),
            duration=duration,
            error_type='FileExtractorException',
            error_message=str(e),
        )
        raise convert_to_http_exception(e)
    except Exception as e:
        # Metrics für Extraktionsfehler
        duration = time.time() - start_time
        record_extraction_error(
            file_path=Path(file.filename) if file.filename else Path('unknown'),
            duration=duration,
            error_type='Exception',
            error_message=str(e),
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
        formats = list_supported_formats()

        # Formate in das erwartete Schema konvertieren
        supported_formats = []
        for format_info in formats:
            for extension in format_info.get('supported_extensions', []):
                mime_types = format_info.get('supported_mime_types', [])
                supported_formats.append(
                    {
                        'extension': extension,
                        'mime_type': mime_types[0]
                        if mime_types
                        else 'application/octet-stream',
                        'description': f'Unterstützt durch {format_info.get("extractor")}',
                        'features': ['text_extraction', 'metadata_extraction'],
                        'max_size': format_info.get('max_file_size'),
                    },
                )

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
            results.append(
                {
                    'filename': file.filename,
                    'success': True,
                    'result': result,
                },
            )
        except Exception as e:
            results.append(
                {
                    'filename': file.filename,
                    'success': False,
                    'error': str(e),
                },
            )

    return {
        'batch_results': results,
        'total_files': len(files),
        'successful_extractions': len([r for r in results if r['success']]),
        'failed_extractions': len([r for r in results if not r['success']]),
    }
