"""
API-Routen für die Datei-Extraktion.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.core.exceptions import FileExtractorException, convert_to_http_exception
from app.extractors import get_extractor, is_format_supported
from app.models.schemas import ErrorResponse, ExtractionResult

router = APIRouter()


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
        # Datei validieren
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail='Kein Dateiname angegeben',
            )

        # Dateigröße prüfen
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f'Datei zu groß. Maximum: {settings.max_file_size} bytes',
            )

        # Temporäre Datei erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            # Datei-Inhalt schreiben
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        try:
            # Datei-Format prüfen
            if not is_format_supported(temp_file_path):
                raise HTTPException(
                    status_code=415,
                    detail=f"Dateiformat '{Path(file.filename).suffix}' wird nicht unterstützt",
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
        raise convert_to_http_exception(e)
    except Exception as e:
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
