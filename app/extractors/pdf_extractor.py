"""
Extraktor für PDF-Dateien.
"""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import PyPDF2
    try:
        from PyPDF2.errors import PdfReadError  # type: ignore[attr-defined]
    except Exception:  # PyPDF2 older versions
        class PdfReadError(Exception):
            pass

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.extractors.base import BaseExtractor
from app.models.schemas import ExtractedText, FileMetadata, StructuredData


class PDFExtractor(BaseExtractor):
    """Extraktor für PDF-Dateien."""

    def __init__(self):
        super().__init__()
        if not PDF_AVAILABLE:
            raise ImportError(
                'PyPDF2 ist nicht installiert. Installieren Sie es mit: pip install PyPDF2',
            )

        self.supported_extensions = ['.pdf']
        self.supported_mime_types = ['application/pdf']
        self.max_file_size = 100 * 1024 * 1024  # 100MB

    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Prüft, ob der Extraktor die PDF-Datei verarbeiten kann."""
        return (
            file_path.suffix.lower() in self.supported_extensions
            or mime_type in self.supported_mime_types
        )

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extrahiert Metadaten aus der PDF-Datei."""
        stat = file_path.stat()

        metadata = FileMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type='application/pdf',
            file_extension='.pdf',
            created_date=datetime.fromtimestamp(stat.st_ctime, tz=UTC),
            modified_date=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

        try:
            with file_path.open('rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # PDF-spezifische Metadaten
                if pdf_reader.metadata:
                    info = pdf_reader.metadata

                    if info.get('/Title'):
                        metadata.title = str(info['/Title'])
                    if info.get('/Author'):
                        metadata.author = str(info['/Author'])
                    if info.get('/Subject'):
                        metadata.subject = str(info['/Subject'])
                    if info.get('/Keywords'):
                        keywords_str = str(info['/Keywords'])
                        metadata.keywords = [k.strip() for k in keywords_str.split(',')]

                # Seitenanzahl
                metadata.page_count = len(pdf_reader.pages)

        except (PdfReadError, OSError, ValueError, AttributeError, TypeError) as e:
            self.logger.warning(
                'PDF metadata extraction failed',
                filename=file_path.name,
                error=str(e),
            )

        return metadata

    def extract_text(self, file_path: Path) -> ExtractedText:
        """Extrahiert Text aus der PDF-Datei."""
        content = ''
        page_texts = []

        try:
            with file_path.open('rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                for _page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            page_texts.append(page_text)
                            content += page_text + '\n'
                    except (PdfReadError, ValueError, AttributeError, TypeError):
                        # Seite überspringen, wenn Text-Extraktion fehlschlägt
                        continue

        except (PdfReadError, OSError, ValueError, AttributeError, TypeError) as err:
            raise RuntimeError('PDF-Extraktion fehlgeschlagen') from err

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
        """Extrahiert strukturierte Daten aus der PDF-Datei."""
        tables = []
        headings = []

        try:
            with file_path.open('rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Überschriften erkennen (einfache Heuristik)
                            page_headings = self._extract_headings(page_text, page_num)
                            headings.extend(page_headings)

                            # Tabellen erkennen (einfache Heuristik)
                            page_tables = self._extract_tables(page_text, page_num)
                            tables.extend(page_tables)

                    except (PdfReadError, ValueError, AttributeError, TypeError):
                        continue

        except (PdfReadError, OSError, ValueError, AttributeError, TypeError) as e:
            self.logger.warning(
                'PDF structured data extraction failed',
                filename=file_path.name,
                error=str(e),
            )

        return StructuredData(
            tables=tables,
            headings=headings,
        )

    def _clean_text(self, text: str) -> str:
        """Bereinigt den extrahierten Text."""
        # Überflüssige Whitespaces entfernen
        text = re.sub(r'\s+', ' ', text)
        # Zeilenumbrüche normalisieren
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # PDF-spezifische Artefakte entfernen
        text = re.sub(r'[^\w\s\.,!?;:()\[\]{}"\'-]', '', text)
        return text.strip()

    def _extract_headings(self, text: str, page_num: int) -> list[dict[str, Any]]:
        """Erkennt Überschriften im Text (einfache Heuristik)."""
        headings = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            line = line.strip()
            if line:
                # Einfache Heuristik für Überschriften
                if (
                    (
                        len(line) < 100  # Kurze Zeilen
                        and line.isupper()
                    )  # Alles Großbuchstaben
                    or (line[0].isupper() and line[-1] not in '.,!?')  # Satz ohne Punkt
                    or re.match(r'^\d+\.\s', line)
                ):  # Nummerierte Liste
                    headings.append(
                        {
                            'level': 1,  # Vereinfachte Hierarchie
                            'text': line,
                            'page': page_num + 1,
                            'position': line_num,
                        },
                    )

        return headings

    def _extract_tables(self, text: str, page_num: int) -> list[dict[str, Any]]:
        """Erkennt Tabellen im Text (einfache Heuristik)."""
        tables = []
        lines = text.split('\n')

        # Einfache Tabellen-Erkennung basierend auf Tabulatoren oder mehreren Leerzeichen
        table_lines = []
        for line in lines:
            if '\t' in line or re.search(r'\s{3,}', line):
                table_lines.append(line)

        if table_lines:
            # Versuche, Tabellen-Struktur zu erkennen
            table_data = {
                'page': page_num + 1,
                'rows': table_lines,
                'row_count': len(table_lines),
                'detection_method': 'whitespace_analysis',
            }
            tables.append(table_data)

        return tables
