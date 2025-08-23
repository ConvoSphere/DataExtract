"""
Validierung und Sicherheit der hochgeladenen Dateien.
"""

from __future__ import annotations

import hashlib
import mimetypes
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import magic
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = get_logger('validation')


class FileValidator:
    """Umfassende Datei-Validierung für Sicherheit und Integrität."""

    def __init__(self):
        self.allowed_extensions = set(settings.allowed_extensions)
        self.max_file_size = settings.max_file_size

        # Gefährliche MIME-Types
        self.dangerous_mime_types = {
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msi',
            'application/x-msdos-program',
            'application/x-msdos-windows',
            'application/x-ms-shortcut',
            'application/x-ms-wim',
        }

        # Erlaubte MIME-Types
        self.allowed_mime_types = {
            # Dokumente
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'application/rtf',
            'application/vnd.oasis.opendocument.text',
            'text/plain',
            # Tabellen
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/vnd.oasis.opendocument.spreadsheet',
            'text/csv',
            # Präsentationen
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint',
            'application/vnd.oasis.opendocument.presentation',
            # Datenformate
            'application/json',
            'application/xml',
            'text/html',
            'application/x-yaml',
            'text/yaml',
            # Bilder
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp',
            'image/svg+xml',
            # Medien
            'video/mp4',
            'video/avi',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-flv',
            'video/webm',
            'audio/mpeg',
            'audio/wav',
            'audio/flac',
            'audio/aac',
            'audio/ogg',
            # Archive
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/x-tar',
            'application/gzip',
        }

    async def validate_upload_file(
        self,
        file: UploadFile,
    ) -> tuple[bool, str, dict | None]:
        """
        Validiert eine hochgeladene Datei umfassend.

        Args:
            file: Die hochgeladene Datei

        Returns:
            Tuple von (is_valid, error_message, file_info)
        """
        try:
            # 1. Basis-Validierung
            if not file.filename:
                return False, 'Kein Dateiname angegeben', None

            # 2. Dateigröße prüfen
            if file.size and file.size > self.max_file_size:
                return (
                    False,
                    f'Datei zu groß. Maximum: {self.max_file_size} bytes',
                    None,
                )

            # 3. Dateiendung prüfen
            file_path = Path(file.filename)
            extension = file_path.suffix.lower()

            if extension not in self.allowed_extensions:
                # Signalisiere 415 Unsupported Media Type via spezielle Nachricht
                return False, f'UNSUPPORTED_EXTENSION:{extension}', None

            # 4. Temporäre Datei erstellen für weitere Validierung
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
            ) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = Path(temp_file.name)

            try:
                # 5. MIME-Type Validierung
                mime_type = self._get_mime_type(temp_file_path)
                if not self._is_mime_type_allowed(mime_type):
                    return False, f'Nicht erlaubter MIME-Type: {mime_type}', None

                # 6. Datei-Signatur prüfen
                if not self._validate_file_signature(temp_file_path, extension):
                    return (
                        False,
                        'Datei-Signatur stimmt nicht mit Dateiendung überein',
                        None,
                    )

                # 7. Malware-Scan (Basic)
                if not self._basic_malware_scan(temp_file_path):
                    return False, 'Datei wurde als verdächtig erkannt', None

                # 8. Datei-Integrität prüfen
                file_hash = self._calculate_file_hash(temp_file_path)

                file_info = {
                    'filename': file.filename,
                    'size': len(content),
                    'extension': extension,
                    'mime_type': mime_type,
                    'hash': file_hash,
                    'temp_path': str(temp_file_path),
                }

                logger.info(
                    'File validation successful',
                    filename=file.filename,
                    size=len(content),
                    mime_type=mime_type,
                    hash=file_hash,
                )

                return True, '', file_info

            finally:
                # Do not delete temp file here; routes are responsible for cleanup
                pass

        except (OSError, ValueError) as e:
            logger.error('File validation error', error=str(e))
            return False, f'Validierungsfehler: {e!s}', None

    def _get_mime_type(self, file_path: Path) -> str:
        """Ermittelt den MIME-Type einer Datei."""
        try:
            # Python-magic für präzise MIME-Type Erkennung
            return magic.from_file(str(file_path), mime=True)
        except (OSError, AttributeError):
            # Fallback: mimetypes Modul
            mime_type, _ = mimetypes.guess_type(str(file_path))
            return mime_type or 'application/octet-stream'

    def _is_mime_type_allowed(self, mime_type: str) -> bool:
        """Prüft, ob ein MIME-Type erlaubt ist."""
        if mime_type in self.dangerous_mime_types:
            logger.warning('Dangerous MIME type detected', mime_type=mime_type)
            return False

        if mime_type not in self.allowed_mime_types:
            logger.warning('Unallowed MIME type', mime_type=mime_type)
            return False

        return True

    def _validate_file_signature(self, file_path: Path, extension: str) -> bool:
        """Validiert die Datei-Signatur (Magic Bytes)."""
        try:
            with file_path.open('rb') as f:
                header = f.read(16)  # Erste 16 Bytes lesen

            # Datei-Signaturen (Magic Bytes)
            signatures = {
                '.pdf': b'%PDF',
                '.docx': b'PK\x03\x04',  # ZIP-Signatur
                '.xlsx': b'PK\x03\x04',  # ZIP-Signatur
                '.pptx': b'PK\x03\x04',  # ZIP-Signatur
                '.zip': b'PK\x03\x04',
                '.jpg': b'\xff\xd8\xff',
                '.jpeg': b'\xff\xd8\xff',
                '.png': b'\x89PNG\r\n\x1a\n',
                '.gif': b'GIF87a' or b'GIF89a',
                '.bmp': b'BM',
                '.tiff': b'II*\x00' or b'MM\x00*',
                '.mp4': b'\x00\x00\x00\x20ftyp',
                '.mp3': b'ID3' or b'\xff\xfb',
                '.wav': b'RIFF',
                '.json': b'{' or b'[',
                '.xml': b'<?xml',
                '.html': b'<!DOCTYPE' or b'<html' or b'<HTML',
                '.txt': None,  # Keine spezifische Signatur
            }

            expected_signature = signatures.get(extension)
            if expected_signature is None:
                return True  # Keine Signatur definiert

            return header.startswith(expected_signature)

        except (OSError, ValueError) as e:
            logger.warning('File signature validation error', error=str(e))
            return True  # Bei Fehlern erlauben

    def _basic_malware_scan(self, file_path: Path) -> bool:
        """Führt einen Basic Malware-Scan durch."""
        try:
            with file_path.open('rb') as f:
                content = f.read()

            # Einfache Heuristiken für verdächtige Inhalte
            suspicious_patterns = [
                b'MZ',  # Windows Executable
                b'PE\x00\x00',  # Portable Executable
                b'ELF',  # Linux Executable
                b'#!/bin/bash',  # Shell Script
                b'<script',  # JavaScript in HTML
                b'javascript:',  # JavaScript Protocol
                b'vbscript:',  # VBScript Protocol
                b'data:text/html',  # Data URI
            ]

            for pattern in suspicious_patterns:
                if pattern in content:
                    logger.warning('Suspicious pattern detected', pattern=str(pattern))
                    return False

            # Prüfe auf verdächtige Dateinamen
            suspicious_names = [
                'virus',
                'malware',
                'trojan',
                'backdoor',
                'exploit',
                'payload',
                'shell',
                'cmd',
                'exec',
                'run',
            ]

            filename_lower = file_path.name.lower()
            for suspicious in suspicious_names:
                if suspicious in filename_lower:
                    logger.warning(
                        'Suspicious filename detected',
                        filename=filename_lower,
                    )
                    return False

            return True

        except (OSError, ValueError) as e:
            logger.warning('Malware scan error', error=str(e))
            return True  # Bei Fehlern erlauben

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Berechnet den SHA-256 Hash einer Datei."""
        try:
            sha256_hash = hashlib.sha256()
            with file_path.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except (OSError, ValueError) as e:
            logger.warning('Hash calculation error', error=str(e))
            return ''

    def cleanup_temp_file(self, temp_path: str) -> None:
        """Löscht eine temporäre Datei."""
        try:
            Path(temp_path).unlink()
        except OSError as e:
            logger.warning(
                'Failed to cleanup temp file',
                temp_path=temp_path,
                error=str(e),
            )


# Globale Validator-Instanz
file_validator = FileValidator()


async def validate_file_upload(file: UploadFile) -> dict:
    """
    Dependency für Datei-Upload-Validierung.

    Args:
        file: Die hochgeladene Datei

    Returns:
        File-Informationen wenn Validierung erfolgreich

    Raises:
        HTTPException: Wenn Validierung fehlschlägt
    """
    is_valid, error_message, file_info = await file_validator.validate_upload_file(file)

    if not is_valid:
        logger.warning('File validation failed', error_message=error_message)
        # Mappe spezifische Validierungsfehler auf passende Statuscodes
        if error_message.startswith('UNSUPPORTED_EXTENSION:'):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f'Nicht unterstützte Dateiendung: {error_message.split(":", 1)[1]}',
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    return file_info
