"""
Basis-Klasse für alle Datei-Extraktoren.
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import (
    InvalidFileException,
    TimeoutException,
)
from app.core.logging import get_logger
from app.models.schemas import (
    ExtractedText,
    ExtractionResult,
    FileMetadata,
    StructuredData,
)


class BaseExtractor(ABC):
    """Basis-Klasse für alle Datei-Extraktoren."""

    def __init__(self):
        self.supported_extensions: list[str] = []
        self.supported_mime_types: list[str] = []
        self.max_file_size: int | None = None
        self.logger = get_logger(f'extractor.{self.__class__.__name__.lower()}')

    @abstractmethod
    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """
        Prüft, ob der Extraktor die gegebene Datei verarbeiten kann.

        Args:
            file_path: Pfad zur Datei
            mime_type: MIME-Type der Datei

        Returns:
            True, wenn die Datei verarbeitet werden kann
        """

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """
        Extrahiert Metadaten aus der Datei.

        Args:
            file_path: Pfad zur Datei

        Returns:
            FileMetadata-Objekt mit den Metadaten
        """

    @abstractmethod
    def extract_text(self, file_path: Path) -> ExtractedText:
        """
        Extrahiert Text aus der Datei.

        Args:
            file_path: Pfad zur Datei

        Returns:
            ExtractedText-Objekt mit dem extrahierten Text
        """

    @abstractmethod
    def extract_structured_data(self, file_path: Path) -> StructuredData:
        """
        Extrahiert strukturierte Daten aus der Datei.

        Args:
            file_path: Pfad zur Datei

        Returns:
            StructuredData-Objekt mit den strukturierten Daten
        """

    def validate_file(self, file_path: Path) -> None:
        """
        Validiert die Datei vor der Extraktion.

        Args:
            file_path: Pfad zur Datei

        Raises:
            InvalidFileException: Wenn die Datei ungültig ist
            FileTooLargeException: Wenn die Datei zu groß ist
        """
        if not file_path.exists():
            raise InvalidFileException(
                str(file_path),
                'Datei existiert nicht',
            )

        if not file_path.is_file():
            raise InvalidFileException(
                str(file_path),
                'Pfad ist keine Datei',
            )

        file_size = file_path.stat().st_size
        max_size = self.max_file_size or settings.max_file_size

        if file_size > max_size:
            from app.core.exceptions import FileTooLargeException

            raise FileTooLargeException(file_size, max_size)

    def extract(
        self,
        file_path: Path,
        include_metadata: bool = True,
        include_text: bool = True,
        include_structure: bool = False,
    ) -> ExtractionResult:
        """
        Führt eine vollständige Extraktion der Datei durch.

        Args:
            file_path: Pfad zur Datei
            include_metadata: Metadaten extrahieren
            include_text: Text extrahieren
            include_structure: Strukturierte Daten extrahieren

        Returns:
            ExtractionResult mit allen extrahierten Daten
        """
        start_time = time.time()
        warnings: list[str] = []
        errors: list[str] = []

        # Logging für Extraktionsstart
        self.logger.info(
            'Extraction started',
            filename=file_path.name,
            file_size=file_path.stat().st_size,
            include_metadata=include_metadata,
            include_text=include_text,
            include_structure=include_structure,
        )

        try:
            # Datei validieren
            self.validate_file(file_path)

            # Metadaten extrahieren
            file_metadata = None
            if include_metadata:
                try:
                    file_metadata = self.extract_metadata(file_path)
                except Exception as e:
                    errors.append(f'Metadaten-Extraktion fehlgeschlagen: {e!s}')
                    self.logger.warning(
                        'Metadata extraction failed',
                        filename=file_path.name,
                        error=str(e),
                    )
                    # Fallback-Metadaten erstellen
                    file_metadata = self._create_fallback_metadata(file_path)

            # Text extrahieren
            extracted_text = None
            if include_text:
                try:
                    extracted_text = self.extract_text(file_path)
                except Exception as e:
                    errors.append(f'Text-Extraktion fehlgeschlagen: {e!s}')
                    self.logger.warning(
                        'Text extraction failed',
                        filename=file_path.name,
                        error=str(e),
                    )

            # Strukturierte Daten extrahieren
            structured_data = None
            if include_structure:
                try:
                    structured_data = self.extract_structured_data(file_path)
                except Exception as e:
                    errors.append(f'Struktur-Extraktion fehlgeschlagen: {e!s}')
                    self.logger.warning(
                        'Structure extraction failed',
                        filename=file_path.name,
                        error=str(e),
                    )

            # Optionale CPU-Last simulieren für Tests (linear mit Dateigröße)
            if (
                settings.simulate_processing
                and not settings.environment == 'production'
            ):
                file_size_kb = max(1, file_path.stat().st_size // 1024)
                # rudimentäre Last: einfache Schleife proportional zur Größe (verstärkt)
                dummy = 0
                for _ in range(min(file_size_kb * 2000, 1000000)):
                    dummy += 1

            extraction_time = time.time() - start_time

            # Timeout prüfen
            if extraction_time > settings.extract_timeout:
                raise TimeoutException(str(file_path), settings.extract_timeout)

            # Logging für erfolgreiche Extraktion
            self.logger.info(
                'Extraction completed',
                filename=file_path.name,
                duration=extraction_time,
                text_length=len(extracted_text.content) if extracted_text else 0,
                word_count=extracted_text.word_count if extracted_text else 0,
                success=len(errors) == 0,
                warnings_count=len(warnings),
                errors_count=len(errors),
            )

            return ExtractionResult(
                success=len(errors) == 0,
                file_metadata=file_metadata,
                extracted_text=extracted_text,
                structured_data=structured_data,
                extraction_time=extraction_time,
                warnings=warnings,
                errors=errors,
            )

        except Exception as e:
            extraction_time = time.time() - start_time
            errors.append(f'Allgemeiner Extraktionsfehler: {e!s}')

            # Logging für Extraktionsfehler
            self.logger.error(
                'Extraction failed',
                filename=file_path.name,
                error_type=type(e).__name__,
                error_message=str(e),
                duration=extraction_time,
            )

            return ExtractionResult(
                success=False,
                file_metadata=self._create_fallback_metadata(file_path),
                extraction_time=extraction_time,
                warnings=warnings,
                errors=errors,
            )

    def _create_fallback_metadata(self, file_path: Path) -> FileMetadata:
        """Erstellt Fallback-Metadaten für eine Datei."""
        import magic

        try:
            mime_type = magic.from_file(str(file_path), mime=True)
        except Exception:
            mime_type = 'application/octet-stream'

        return FileMetadata(
            filename=file_path.name,
            file_size=file_path.stat().st_size,
            file_type=mime_type,
            file_extension=file_path.suffix.lower(),
        )

    def get_supported_formats(self) -> dict[str, Any]:
        """Gibt Informationen über unterstützte Formate zurück."""
        return {
            'extensions': self.supported_extensions,
            'mime_types': self.supported_mime_types,
            'max_file_size': self.max_file_size,
        }
