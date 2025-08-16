"""
Apache Tika-basierter Extraktor als letzter Fallback.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.extractors.base import BaseExtractor
from app.models.schemas import ExtractedText, FileMetadata, StructuredData


class TikaExtractor(BaseExtractor):
    """Extraktor, der Apache Tika Server via REST anspricht."""

    def __init__(self) -> None:
        super().__init__()
        # Breite Abdeckung – Tika unterstützt viele Formate. Wir setzen hier keine harte Liste,
        # lassen aber optionale Präferenzen aus Settings zu.
        self.supported_extensions = settings.allowed_extensions
        self.supported_mime_types = []
        self.max_file_size = settings.max_file_size

        # HTTP-Client mit Timeouts
        self._client = httpx.Client(
            base_url=settings.tika_server_url,
            timeout=settings.tika_timeout,
        )

    def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Tika darf grundsätzlich alles verarbeiten, wird aber als letzter Fallback genutzt."""
        # Falls bestimmte Formate bevorzugt geroutet werden sollen
        prefer = set(ext.lower() for ext in settings.tika_prefer_for_formats or [])
        if file_path.suffix.lower() in prefer or mime_type.lower() in prefer:
            return True
        # Sonst: generisch ja, aber die Factory-Order stellt sicher, dass Tika zuletzt greift
        return True

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        stat = file_path.stat()
        metadata = FileMetadata(
            filename=file_path.name,
            file_size=stat.st_size,
            file_type=self._guess_mime(file_path),
            file_extension=file_path.suffix.lower(),
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
        )

        try:
            headers = {'Accept': 'application/json'}
            with open(file_path, 'rb') as f:
                resp = self._client.put('/meta', headers=headers, content=f)
            resp.raise_for_status()
            data = resp.json()

            # Häufige Tika-Felder mappen (variieren je nach Parser)
            metadata.title = _first_of(data, ['dc:title', 'title', 'pdf:docinfo:title'])
            metadata.author = _first_of(data, ['Author', 'meta:author', 'dc:creator'])
            metadata.subject = _first_of(data, ['subject', 'dc:subject'])
            keywords = _first_of(data, ['Keywords', 'pdf:docinfo:keywords', 'dc:subject'])
            if isinstance(keywords, str):
                metadata.keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            page_count = _first_of(data, ['xmpTPg:NPages', 'Page-Count'])
            if page_count is not None:
                try:
                    metadata.page_count = int(page_count)
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning('Tika metadata extraction failed', filename=file_path.name, error=str(e))

        return metadata

    def extract_text(self, file_path: Path) -> ExtractedText:
        content = ''
        ocr_used = False
        ocr_confidence = None

        try:
            headers = {'Accept': 'text/plain; charset=UTF-8'}
            if settings.tika_use_ocr:
                headers.update(
                    {
                        'X-Tika-OCRLanguage': settings.tika_ocr_langs,
                        'X-Tika-PDFextractInlineImages': 'true',
                        'X-Tika-OCRTimeout': str(max(1, settings.tika_timeout - 1)),
                    }
                )
            with open(file_path, 'rb') as f:
                resp = self._client.put('/tika', headers=headers, content=f)
            resp.raise_for_status()
            content = resp.text or ''
            if settings.tika_use_ocr:
                ocr_used = True
        except Exception as e:
            raise Exception(f'Tika-Text-Extraktion fehlgeschlagen: {e!s}')

        word_count = len(content.split()) if content else 0
        character_count = len(content)
        return ExtractedText(
            content=content,
            word_count=word_count,
            character_count=character_count,
            ocr_used=ocr_used,
            ocr_confidence=ocr_confidence,
        )

    def extract_structured_data(self, file_path: Path) -> StructuredData:
        # Basis: Tika liefert primär Text/Metadaten. Strukturierte Daten bleiben leer.
        return StructuredData()

    def _guess_mime(self, file_path: Path) -> str:
        try:
            import magic  # type: ignore

            return magic.from_file(str(file_path), mime=True)
        except Exception:
            return 'application/octet-stream'


def _first_of(data: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        val = data.get(key)
        if isinstance(val, list) and val:
            return str(val[0])
        if isinstance(val, str) and val.strip():
            return val
    return None