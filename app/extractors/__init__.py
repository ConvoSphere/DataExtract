"""
Extraktoren-Package für die Universal File Extractor API.
"""

import importlib
from pathlib import Path
from typing import Dict, List, Optional, Type
import magic

from app.extractors.base import BaseExtractor
from app.core.exceptions import UnsupportedFileFormatException


class ExtractorFactory:
    """Factory für Datei-Extraktoren."""
    
    def __init__(self):
        self._extractors: Dict[str, Type[BaseExtractor]] = {}
        self._load_extractors()
    
    def _load_extractors(self) -> None:
        """Lädt alle verfügbaren Extraktoren."""
        try:
            from app.extractors.text_extractor import TextExtractor
            self._register_extractor(TextExtractor())
        except ImportError as e:
            print(f"Warnung: TextExtractor konnte nicht geladen werden: {e}")
        
        try:
            from app.extractors.pdf_extractor import PDFExtractor
            self._register_extractor(PDFExtractor())
        except ImportError as e:
            print(f"Warnung: PDFExtractor konnte nicht geladen werden: {e}")
        
        try:
            from app.extractors.docx_extractor import DOCXExtractor
            self._register_extractor(DOCXExtractor())
        except ImportError as e:
            print(f"Warnung: DOCXExtractor konnte nicht geladen werden: {e}")
        
        try:
            from app.extractors.image_extractor import ImageExtractor
            self._register_extractor(ImageExtractor())
        except ImportError as e:
            print(f"Warnung: ImageExtractor konnte nicht geladen werden: {e}")
        
        try:
            from app.extractors.media_extractor import MediaExtractor
            self._register_extractor(MediaExtractor())
        except ImportError as e:
            print(f"Warnung: MediaExtractor konnte nicht geladen werden: {e}")
    
    def _register_extractor(self, extractor: BaseExtractor) -> None:
        """Registriert einen Extraktor."""
        for extension in extractor.supported_extensions:
            self._extractors[extension.lower()] = type(extractor)
        
        for mime_type in extractor.supported_mime_types:
            self._extractors[mime_type] = type(extractor)
    
    def get_extractor(self, file_path: Path) -> BaseExtractor:
        """
        Gibt den passenden Extraktor für eine Datei zurück.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Passender Extraktor
            
        Raises:
            UnsupportedFileFormatException: Wenn kein passender Extraktor gefunden wird
        """
        # Versuche MIME-Type zu ermitteln
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
        except Exception:
            mime_type = "application/octet-stream"
        
        # Prüfe zuerst nach MIME-Type
        if mime_type in self._extractors:
            extractor_class = self._extractors[mime_type]
            return extractor_class()
        
        # Prüfe nach Dateiendung
        extension = file_path.suffix.lower()
        if extension in self._extractors:
            extractor_class = self._extractors[extension]
            return extractor_class()
        
        # Kein passender Extraktor gefunden
        raise UnsupportedFileFormatException(extension)
    
    def get_supported_formats(self) -> List[Dict[str, any]]:
        """Gibt alle unterstützten Formate zurück."""
        formats = []
        
        for key, extractor_class in self._extractors.items():
            try:
                extractor = extractor_class()
                format_info = extractor.get_supported_formats()
                
                # Nur einmal pro Extraktor-Klasse hinzufügen
                if not any(f.get("class") == extractor_class.__name__ for f in formats):
                    formats.append({
                        "class": extractor_class.__name__,
                        "extensions": format_info.get("extensions", []),
                        "mime_types": format_info.get("mime_types", []),
                        "max_file_size": format_info.get("max_file_size")
                    })
            except Exception:
                continue
        
        return formats
    
    def is_format_supported(self, file_path: Path) -> bool:
        """Prüft, ob ein Dateiformat unterstützt wird."""
        try:
            self.get_extractor(file_path)
            return True
        except UnsupportedFileFormatException:
            return False


# Globale Factory-Instanz
extractor_factory = ExtractorFactory()


def get_extractor(file_path: Path) -> BaseExtractor:
    """Hilfsfunktion zum Abrufen eines Extraktors."""
    return extractor_factory.get_extractor(file_path)


def get_supported_formats() -> List[Dict[str, any]]:
    """Hilfsfunktion zum Abrufen unterstützter Formate."""
    return extractor_factory.get_supported_formats()


def is_format_supported(file_path: Path) -> bool:
    """Hilfsfunktion zum Prüfen der Format-Unterstützung."""
    return extractor_factory.is_format_supported(file_path)