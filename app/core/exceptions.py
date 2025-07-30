"""
Benutzerdefinierte Exceptions für die Universal File Extractor API.
"""

from typing import Any

from fastapi import HTTPException, status


class FileExtractorException(Exception):
    """Basis-Exception für alle File Extractor Fehler."""

    def __init__(
        self,
        message: str,
        error_code: str = 'UNKNOWN_ERROR',
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class UnsupportedFileFormatException(FileExtractorException):
    """Exception für nicht unterstützte Dateiformate."""

    def __init__(self, file_extension: str):
        super().__init__(
            message=f"Dateiformat '{file_extension}' wird nicht unterstützt",
            error_code='UNSUPPORTED_FORMAT',
            details={'file_extension': file_extension},
        )


class FileTooLargeException(FileExtractorException):
    """Exception für zu große Dateien."""

    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f'Datei ist zu groß ({file_size} bytes). Maximum: {max_size} bytes',
            error_code='FILE_TOO_LARGE',
            details={'file_size': file_size, 'max_size': max_size},
        )


class ExtractionFailedException(FileExtractorException):
    """Exception für fehlgeschlagene Extraktionen."""

    def __init__(self, file_name: str, reason: str):
        super().__init__(
            message=f"Extraktion von '{file_name}' fehlgeschlagen: {reason}",
            error_code='EXTRACTION_FAILED',
            details={'file_name': file_name, 'reason': reason},
        )


class InvalidFileException(FileExtractorException):
    """Exception für ungültige oder beschädigte Dateien."""

    def __init__(self, file_name: str, reason: str):
        super().__init__(
            message=f"Ungültige Datei '{file_name}': {reason}",
            error_code='INVALID_FILE',
            details={'file_name': file_name, 'reason': reason},
        )


class TimeoutException(FileExtractorException):
    """Exception für Timeouts bei der Extraktion."""

    def __init__(self, file_name: str, timeout_seconds: int):
        super().__init__(
            message=f"Extraktion von '{file_name}' hat das Timeout von {timeout_seconds}s überschritten",
            error_code='EXTRACTION_TIMEOUT',
            details={'file_name': file_name, 'timeout_seconds': timeout_seconds},
        )


def convert_to_http_exception(exc: FileExtractorException) -> HTTPException:
    """Konvertiert eine FileExtractorException zu einer HTTPException."""

    error_mapping = {
        'UNSUPPORTED_FORMAT': status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        'FILE_TOO_LARGE': status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        'EXTRACTION_FAILED': status.HTTP_422_UNPROCESSABLE_ENTITY,
        'INVALID_FILE': status.HTTP_400_BAD_REQUEST,
        'EXTRACTION_TIMEOUT': status.HTTP_408_REQUEST_TIMEOUT,
        'UNKNOWN_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    status_code = error_mapping.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HTTPException(
        status_code=status_code,
        detail={
            'error': exc.error_code,
            'message': exc.message,
            'details': exc.details,
        },
    )
