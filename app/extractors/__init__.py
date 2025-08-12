"""
Factory für Datei-Extraktoren.
"""

from pathlib import Path
from typing import List, Optional

import magic

from app.extractors.base import BaseExtractor


class ExtractorFactory:
    """Factory für Datei-Extraktoren."""

    def __init__(self):
        self.extractors: list[tuple[BaseExtractor, int]] = []  # (extractor, priority)
        self._load_extractors()

    def _load_extractors(self) -> None:
        """Lädt alle verfügbaren Extraktoren."""
        # Docling-Extraktor als primärer Extraktor (falls verfügbar)
        try:
            from app.extractors.docling_extractor import DoclingExtractor

            self._register_extractor(DoclingExtractor(), priority=1)  # Höhere Priorität
        except ImportError:
            pass

        # Fallback-Extraktoren
        try:
            from app.extractors.text_extractor import TextExtractor

            self._register_extractor(TextExtractor(), priority=10)
        except ImportError:
            pass

        try:
            from app.extractors.pdf_extractor import PDFExtractor

            self._register_extractor(PDFExtractor(), priority=10)
        except ImportError:
            pass

        try:
            from app.extractors.docx_extractor import DOCXExtractor

            self._register_extractor(DOCXExtractor(), priority=10)
        except ImportError:
            pass

        try:
            from app.extractors.image_extractor import ImageExtractor

            self._register_extractor(ImageExtractor(), priority=10)
        except ImportError:
            pass

        try:
            from app.extractors.media_extractor import MediaExtractor

            self._register_extractor(MediaExtractor(), priority=10)
        except ImportError:
            pass

    def _register_extractor(self, extractor: BaseExtractor, priority: int = 10) -> None:
        """Registriert einen Extraktor mit Priorität."""
        self.extractors.append((extractor, priority))
        # Nach Priorität sortieren (niedrigere Zahl = höhere Priorität)
        self.extractors.sort(key=lambda x: x[1])

    def get_extractor(self, file_path: Path) -> BaseExtractor | None:
        """Gibt den passenden Extraktor für eine Datei zurück."""
        try:
            # MIME-Type ermitteln
            mime_type = magic.from_file(str(file_path), mime=True)
        except Exception:
            mime_type = 'application/octet-stream'

        # Extraktor mit höchster Priorität finden
        for extractor, _priority in self.extractors:
            if extractor.can_extract(file_path, mime_type):
                return extractor

        return None

    def get_all_extractors(self) -> list[BaseExtractor]:
        """Gibt alle registrierten Extraktoren zurück."""
        return [extractor for extractor, _ in self.extractors]

    def get_supported_formats(self) -> list[dict]:
        """Gibt alle unterstützten Formate zurück."""
        formats = []
        for extractor, priority in self.extractors:
            formats.append(
                {
                    'extractor': extractor.__class__.__name__,
                    'priority': priority,
                    'supported_extensions': extractor.supported_extensions,
                    'supported_mime_types': extractor.supported_mime_types,
                    'max_file_size': extractor.max_file_size,
                },
            )
        return formats


# Globale Factory-Instanz
_extractor_factory = ExtractorFactory()


def get_extractor(file_path: Path) -> BaseExtractor:
    """Gibt den passenden Extraktor für eine Datei zurück."""
    extractor = _extractor_factory.get_extractor(file_path)
    if not extractor:
        raise ValueError(f'Kein Extraktor für Datei {file_path} gefunden')
    return extractor


def get_all_extractors() -> list[BaseExtractor]:
    """Gibt alle registrierten Extraktoren zurück."""
    return _extractor_factory.get_all_extractors()


def get_supported_formats() -> list[dict]:
    """Gibt alle unterstützten Formate zurück."""
    return _extractor_factory.get_supported_formats()


def is_format_supported(file_path: Path) -> bool:
    """Prüft, ob ein Dateiformat unterstützt wird."""
    return _extractor_factory.get_extractor(file_path) is not None
