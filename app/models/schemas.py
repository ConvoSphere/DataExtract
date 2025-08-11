"""
Pydantic-Schemas für die Universal File Extractor API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """Request-Modell für Datei-Extraktion."""

    include_metadata: bool = Field(
        default=True,
        description='Metadaten der Datei einschließen',
    )
    include_text: bool = Field(
        default=True,
        description='Text-Inhalt extrahieren',
    )
    include_structure: bool = Field(
        default=False,
        description='Strukturierte Daten extrahieren',
    )
    include_images: bool = Field(
        default=False,
        description='Bilder extrahieren',
    )
    include_media: bool = Field(
        default=False,
        description='Medien extrahieren',
    )
    language: str | None = Field(
        default=None,
        description='Sprache für die Extraktion (ISO 639-1)',
    )
    async_processing: bool = Field(
        default=False,
        description='Asynchrone Verarbeitung verwenden',
    )


class FileMetadata(BaseModel):
    """Metadaten einer Datei."""

    filename: str = Field(description='Name der Datei')
    file_size: int = Field(description='Größe der Datei in Bytes')
    file_type: str = Field(description='MIME-Type der Datei')
    file_extension: str = Field(description='Dateiendung')
    created_date: datetime | None = Field(
        default=None,
        description='Erstellungsdatum',
    )
    modified_date: datetime | None = Field(
        default=None,
        description='Änderungsdatum',
    )
    page_count: int | None = Field(
        default=None,
        description='Anzahl der Seiten (für Dokumente)',
    )
    author: str | None = Field(
        default=None,
        description='Autor des Dokuments',
    )
    title: str | None = Field(
        default=None,
        description='Titel des Dokuments',
    )
    subject: str | None = Field(
        default=None,
        description='Betreff des Dokuments',
    )
    keywords: list[str] | None = Field(
        default=None,
        description='Schlüsselwörter',
    )
    # Neue Felder für erweiterte Metadaten
    dimensions: dict[str, int] | None = Field(
        default=None,
        description='Dimensionen (für Bilder/Medien)',
    )
    duration: float | None = Field(
        default=None,
        description='Dauer in Sekunden (für Medien)',
    )
    bitrate: int | None = Field(
        default=None,
        description='Bitrate (für Medien)',
    )
    resolution: str | None = Field(
        default=None,
        description='Auflösung (für Bilder/Medien)',
    )
    color_space: str | None = Field(
        default=None,
        description='Farbraum (für Bilder)',
    )


class ExtractedText(BaseModel):
    """Extrahierter Text-Inhalt."""

    content: str = Field(description='Extrahierter Text')
    language: str | None = Field(
        default=None,
        description='Erkannte Sprache',
    )
    confidence: float | None = Field(
        default=None,
        description='Konfidenz der Texterkennung (0-1)',
    )
    word_count: int | None = Field(
        default=None,
        description='Anzahl der Wörter',
    )
    character_count: int | None = Field(
        default=None,
        description='Anzahl der Zeichen',
    )
    # Neue Felder für OCR
    ocr_used: bool = Field(
        default=False,
        description='OCR wurde verwendet',
    )
    ocr_confidence: float | None = Field(
        default=None,
        description='OCR-Konfidenz (0-1)',
    )


class ExtractedImage(BaseModel):
    """Extrahierte Bild-Informationen."""

    image_index: int = Field(description='Index des Bildes')
    image_type: str = Field(description='Typ des Bildes (jpeg, png, etc.)')
    dimensions: dict[str, int] = Field(description='Dimensionen (width, height)')
    file_size: int = Field(description='Größe in Bytes')
    extracted_text: str | None = Field(
        default=None,
        description='Extrahierter Text aus dem Bild (OCR)',
    )
    ocr_confidence: float | None = Field(
        default=None,
        description='OCR-Konfidenz',
    )
    color_palette: list[str] | None = Field(
        default=None,
        description='Dominante Farben',
    )


class ExtractedMedia(BaseModel):
    """Extrahierte Medien-Informationen."""

    media_type: str = Field(description='Typ (video, audio)')
    format: str = Field(description='Format (mp4, mp3, etc.)')
    duration: float = Field(description='Dauer in Sekunden')
    bitrate: int | None = Field(
        default=None,
        description='Bitrate',
    )
    resolution: str | None = Field(
        default=None,
        description='Auflösung (für Video)',
    )
    fps: float | None = Field(
        default=None,
        description='Frames pro Sekunde (für Video)',
    )
    channels: int | None = Field(
        default=None,
        description='Anzahl Kanäle (für Audio)',
    )
    sample_rate: int | None = Field(
        default=None,
        description='Sample Rate (für Audio)',
    )
    transcript: str | None = Field(
        default=None,
        description='Audio-Transkript',
    )


class StructuredData(BaseModel):
    """Strukturierte Daten aus der Datei."""

    tables: list[dict[str, Any]] | None = Field(
        default=None,
        description='Extrahierte Tabellen',
    )
    lists: list[list[str]] | None = Field(
        default=None,
        description='Extrahierte Listen',
    )
    headings: list[dict[str, Any]] | None = Field(
        default=None,
        description='Überschriften mit Hierarchie',
    )
    links: list[str] | None = Field(
        default=None,
        description='Extrahierte Links',
    )
    images: list[ExtractedImage] | None = Field(
        default=None,
        description='Extrahierte Bilder',
    )
    media: list[ExtractedMedia] | None = Field(
        default=None,
        description='Extrahierte Medien',
    )
    # Neue Felder für erweiterte Strukturen
    slides: list[dict[str, Any]] | None = Field(
        default=None,
        description='Präsentationsfolien',
    )
    charts: list[dict[str, Any]] | None = Field(
        default=None,
        description='Diagramme und Charts',
    )
    forms: list[dict[str, Any]] | None = Field(
        default=None,
        description='Formulare',
    )


class ExtractionResult(BaseModel):
    """Ergebnis einer Datei-Extraktion."""

    success: bool = Field(description='Erfolg der Extraktion')
    file_metadata: FileMetadata = Field(description='Datei-Metadaten')
    extracted_text: ExtractedText | None = Field(
        default=None,
        description='Extrahierter Text',
    )
    structured_data: StructuredData | None = Field(
        default=None,
        description='Strukturierte Daten',
    )
    extraction_time: float = Field(description='Extraktionszeit in Sekunden')
    warnings: list[str] = Field(
        default_factory=list,
        description='Warnungen während der Extraktion',
    )
    errors: list[str] = Field(
        default_factory=list,
        description='Fehler während der Extraktion',
    )
    # Neue Felder für asynchrone Verarbeitung
    job_id: str | None = Field(
        default=None,
        description='Job-ID für asynchrone Verarbeitung',
    )
    processing_status: str | None = Field(
        default=None,
        description='Verarbeitungsstatus',
    )


class AsyncExtractionRequest(BaseModel):
    """Request für asynchrone Extraktion."""

    callback_url: str | None = Field(
        default=None,
        description='Callback-URL für Benachrichtigungen',
    )
    priority: str = Field(
        default='normal',
        description='Priorität (low, normal, high)',
    )
    retention_hours: int = Field(
        default=24,
        description='Aufbewahrungszeit in Stunden',
    )


class AsyncExtractionResponse(BaseModel):
    """Response für asynchrone Extraktion."""

    job_id: str = Field(description='Job-ID')
    status: str = Field(description='Status (queued, processing, completed, failed)')
    estimated_completion: datetime | None = Field(
        default=None,
        description='Geschätzte Fertigstellung',
    )
    progress: float | None = Field(
        default=None,
        description='Fortschritt (0-100)',
    )
    result_url: str | None = Field(
        default=None,
        description='URL zum Abrufen des Ergebnisses',
    )


class JobStatus(BaseModel):
    """Status eines asynchronen Jobs."""

    job_id: str = Field(description='Job-ID')
    status: str = Field(description='Status')
    created_at: datetime = Field(description='Erstellungszeit')
    started_at: datetime | None = Field(
        default=None,
        description='Startzeit',
    )
    completed_at: datetime | None = Field(
        default=None,
        description='Fertigstellungszeit',
    )
    progress: float = Field(description='Fortschritt (0-100)')
    result: ExtractionResult | None = Field(
        default=None,
        description='Extraktionsergebnis',
    )
    error: str | None = Field(
        default=None,
        description='Fehlermeldung',
    )


class SupportedFormat(BaseModel):
    """Informationen über ein unterstütztes Dateiformat."""

    extension: str = Field(description='Dateiendung')
    mime_type: str = Field(description='MIME-Type')
    description: str = Field(description='Beschreibung des Formats')
    features: list[str] = Field(description='Unterstützte Features')
    max_size: int | None = Field(
        default=None,
        description='Maximale Dateigröße in Bytes',
    )
    # Neue Felder
    category: str = Field(description='Kategorie (document, image, media, archive)')
    extraction_methods: list[str] = Field(
        default_factory=list,
        description='Verwendete Extraktionsmethoden',
    )


class FormatsResponse(BaseModel):
    """Response für unterstützte Formate."""

    formats: list[SupportedFormat] = Field(description='Liste unterstützter Formate')
    total_count: int = Field(description='Anzahl unterstützter Formate')
    categories: dict[str, int] = Field(description='Anzahl pro Kategorie')


class HealthResponse(BaseModel):
    """Health-Check Response."""

    status: str = Field(description='Status der API')
    version: str = Field(description='API-Version')
    timestamp: datetime = Field(description='Zeitstempel')
    uptime: float = Field(description='Uptime in Sekunden')
    supported_formats_count: int = Field(description='Anzahl unterstützter Formate')
    # Neue Felder (optional mit Defaults)
    active_jobs: int = Field(default=0, description='Aktive Jobs')
    queue_size: int = Field(default=0, description='Warteschlangengröße')
    worker_status: str = Field(default='unknown', description='Worker-Status')


class ErrorResponse(BaseModel):
    """Standard-Fehler-Response."""

    error: str = Field(description='Fehlercode')
    message: str = Field(description='Fehlermeldung')
    details: dict[str, Any] | None = Field(
        default=None,
        description='Zusätzliche Fehlerdetails',
    )
    timestamp: datetime = Field(description='Zeitstempel des Fehlers')
    job_id: str | None = Field(
        default=None,
        description='Job-ID (bei asynchronen Fehlern)',
    )
