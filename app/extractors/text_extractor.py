"""
Extraktor für einfache Textdateien (TXT, CSV, JSON, XML).
"""

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from defusedxml import ElementTree as ElementTree

from app.extractors.base import BaseExtractor
from app.models.schemas import ExtractedText, FileMetadata, StructuredData


class TextExtractor(BaseExtractor):
    """Extraktor für einfache Textdateien."""

    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.txt', '.csv', '.json', '.xml', '.html', '.htm']
        self.supported_mime_types = [
            'text/plain',
            'text/csv',
            'application/json',
            'application/xml',
            'text/html',
            'text/xml',
        ]
        self.max_file_size = 50 * 1024 * 1024  # 50MB

    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Prüft, ob der Extraktor die Datei verarbeiten kann."""
        return (
            file_path.suffix.lower() in self.supported_extensions
            or mime_type in self.supported_mime_types
        )

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extrahiert Metadaten aus der Textdatei."""
        stat = file_path.stat()

        metadata = FileMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type=self._get_mime_type(file_path),
            file_extension=file_path.suffix.lower(),
            created_date=datetime.fromtimestamp(stat.st_ctime, tz=UTC),
            modified_date=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

        # Zusätzliche Metadaten basierend auf Dateityp
        if file_path.suffix.lower() == '.json':
            try:
                with file_path.open(encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        metadata.title = data.get('title') or data.get('name')
                        metadata.author = data.get('author') or data.get('creator')
                        metadata.subject = data.get('subject') or data.get(
                            'description',
                        )
            except (OSError, ValueError, TypeError):
                pass

        return metadata

    def extract_text(self, file_path: Path) -> ExtractedText:
        """Extrahiert Text aus der Datei."""
        try:
            with file_path.open(encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback für andere Encodings
            try:
                with file_path.open(encoding='latin-1') as f:
                    content = f.read()
            except (OSError, ValueError):
                content = ''

        # Text bereinigen
        content = self._clean_text(content)

        # Statistiken berechnen
        word_count = len(content.split()) if content else 0
        character_count = len(content)

        return ExtractedText(
            content=content,
            word_count=word_count,
            character_count=character_count,
        )

    def extract_structured_data(self, file_path: Path) -> StructuredData:
        """Extrahiert strukturierte Daten basierend auf Dateityp."""
        extension = file_path.suffix.lower()

        if extension == '.csv':
            return self._extract_csv_structure(file_path)
        if extension == '.json':
            return self._extract_json_structure(file_path)
        if extension in ['.xml', '.html', '.htm']:
            return self._extract_xml_structure(file_path)
        return StructuredData()

    def _get_mime_type(self, file_path: Path) -> str:
        """Ermittelt den MIME-Type der Datei."""
        extension = file_path.suffix.lower()
        mime_types = {
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.htm': 'text/html',
        }
        return mime_types.get(extension, 'text/plain')

    def _clean_text(self, text: str) -> str:
        """Bereinigt den Text."""
        # Überflüssige Whitespaces entfernen
        text = re.sub(r'\s+', ' ', text)
        # Zeilenumbrüche normalisieren
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()

    def _extract_csv_structure(self, file_path: Path) -> StructuredData:
        """Extrahiert Struktur aus CSV-Dateien."""
        tables = []

        try:
            with file_path.open(encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, [])

                if headers:
                    table_data = {
                        'headers': headers,
                        'rows': list(reader),
                        'row_count': len(list(reader)),
                        'column_count': len(headers),
                    }
                    tables.append(table_data)
        except (OSError, ValueError, TypeError):
            pass

        return StructuredData(tables=tables)

    def _extract_json_structure(self, file_path: Path) -> StructuredData:
        """Extrahiert Struktur aus JSON-Dateien."""
        try:
            with file_path.open(encoding='utf-8') as f:
                data = json.load(f)

            # Einfache Struktur-Analyse
            structure_info = {
                'type': type(data).__name__,
                'keys': list(data.keys()) if isinstance(data, dict) else None,
                'length': len(data) if hasattr(data, '__len__') else None,
            }

            return StructuredData(
                tables=[{'structure': structure_info}],
            )
        except (OSError, ValueError, TypeError):
            return StructuredData()

    def _extract_xml_structure(self, file_path: Path) -> StructuredData:
        """Extrahiert Struktur aus XML/HTML-Dateien."""
        try:
            tree = ElementTree.parse(file_path)
            root = tree.getroot()

            # Links extrahieren
            links = []
            for elem in root.iter():
                if elem.tag.endswith('a') and elem.get('href'):
                    links.append(elem.get('href'))

            # Überschriften extrahieren
            headings = []
            for i, elem in enumerate(root.iter()):
                if elem.tag.endswith(('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
                    headings.append(
                        {
                            'level': int(elem.tag[-1]),
                            'text': elem.text or '',
                            'position': i,
                        },
                    )

            return StructuredData(
                links=links,
                headings=headings,
            )
        except (OSError, ValueError, TypeError):
            return StructuredData()
