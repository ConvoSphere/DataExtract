"""
Pydantic-Schemas für die Universal File Extractor API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """Request-Modell für Datei-Extraktion."""
    
    include_metadata: bool = Field(
        default=True,
        description="Metadaten der Datei einschließen"
    )
    include_text: bool = Field(
        default=True,
        description="Text-Inhalt extrahieren"
    )
    include_structure: bool = Field(
        default=False,
        description="Strukturierte Daten extrahieren"
    )
    include_images: bool = Field(
        default=False,
        description="Bilder extrahieren"
    )
    include_media: bool = Field(
        default=False,
        description="Medien extrahieren"
    )
    language: Optional[str] = Field(
        default=None,
        description="Sprache für die Extraktion (ISO 639-1)"
    )
    async_processing: bool = Field(
        default=False,
        description="Asynchrone Verarbeitung verwenden"
    )


class FileMetadata(BaseModel):
    """Metadaten einer Datei."""
    
    filename: str = Field(description="Name der Datei")
    file_size: int = Field(description="Größe der Datei in Bytes")
    file_type: str = Field(description="MIME-Type der Datei")
    file_extension: str = Field(description="Dateiendung")
    created_date: Optional[datetime] = Field(
        default=None,
        description="Erstellungsdatum"
    )
    modified_date: Optional[datetime] = Field(
        default=None,
        description="Änderungsdatum"
    )
    page_count: Optional[int] = Field(
        default=None,
        description="Anzahl der Seiten (für Dokumente)"
    )
    author: Optional[str] = Field(
        default=None,
        description="Autor des Dokuments"
    )
    title: Optional[str] = Field(
        default=None,
        description="Titel des Dokuments"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Betreff des Dokuments"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Schlüsselwörter"
    )
    # Neue Felder für erweiterte Metadaten
    dimensions: Optional[Dict[str, int]] = Field(
        default=None,
        description="Dimensionen (für Bilder/Medien)"
    )
    duration: Optional[float] = Field(
        default=None,
        description="Dauer in Sekunden (für Medien)"
    )
    bitrate: Optional[int] = Field(
        default=None,
        description="Bitrate (für Medien)"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Auflösung (für Bilder/Medien)"
    )
    color_space: Optional[str] = Field(
        default=None,
        description="Farbraum (für Bilder)"
    )


class ExtractedText(BaseModel):
    """Extrahierter Text-Inhalt."""
    
    content: str = Field(description="Extrahierter Text")
    language: Optional[str] = Field(
        default=None,
        description="Erkannte Sprache"
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Konfidenz der Texterkennung (0-1)"
    )
    word_count: Optional[int] = Field(
        default=None,
        description="Anzahl der Wörter"
    )
    character_count: Optional[int] = Field(
        default=None,
        description="Anzahl der Zeichen"
    )
    # Neue Felder für OCR
    ocr_used: bool = Field(
        default=False,
        description="OCR wurde verwendet"
    )
    ocr_confidence: Optional[float] = Field(
        default=None,
        description="OCR-Konfidenz (0-1)"
    )


class ExtractedImage(BaseModel):
    """Extrahierte Bild-Informationen."""
    
    image_index: int = Field(description="Index des Bildes")
    image_type: str = Field(description="Typ des Bildes (jpeg, png, etc.)")
    dimensions: Dict[str, int] = Field(description="Dimensionen (width, height)")
    file_size: int = Field(description="Größe in Bytes")
    extracted_text: Optional[str] = Field(
        default=None,
        description="Extrahierter Text aus dem Bild (OCR)"
    )
    ocr_confidence: Optional[float] = Field(
        default=None,
        description="OCR-Konfidenz"
    )
    color_palette: Optional[List[str]] = Field(
        default=None,
        description="Dominante Farben"
    )


class ExtractedMedia(BaseModel):
    """Extrahierte Medien-Informationen."""
    
    media_type: str = Field(description="Typ (video, audio)")
    format: str = Field(description="Format (mp4, mp3, etc.)")
    duration: float = Field(description="Dauer in Sekunden")
    bitrate: Optional[int] = Field(
        default=None,
        description="Bitrate"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Auflösung (für Video)"
    )
    fps: Optional[float] = Field(
        default=None,
        description="Frames pro Sekunde (für Video)"
    )
    channels: Optional[int] = Field(
        default=None,
        description="Anzahl Kanäle (für Audio)"
    )
    sample_rate: Optional[int] = Field(
        default=None,
        description="Sample Rate (für Audio)"
    )
    transcript: Optional[str] = Field(
        default=None,
        description="Audio-Transkript"
    )


class StructuredData(BaseModel):
    """Strukturierte Daten aus der Datei."""
    
    tables: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Extrahierte Tabellen"
    )
    lists: Optional[List[List[str]]] = Field(
        default=None,
        description="Extrahierte Listen"
    )
    headings: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Überschriften mit Hierarchie"
    )
    links: Optional[List[str]] = Field(
        default=None,
        description="Extrahierte Links"
    )
    images: Optional[List[ExtractedImage]] = Field(
        default=None,
        description="Extrahierte Bilder"
    )
    media: Optional[List[ExtractedMedia]] = Field(
        default=None,
        description="Extrahierte Medien"
    )
    # Neue Felder für erweiterte Strukturen
    slides: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Präsentationsfolien"
    )
    charts: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Diagramme und Charts"
    )
    forms: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Formulare"
    )


class ExtractionResult(BaseModel):
    """Ergebnis einer Datei-Extraktion."""
    
    success: bool = Field(description="Erfolg der Extraktion")
    file_metadata: FileMetadata = Field(description="Datei-Metadaten")
    extracted_text: Optional[ExtractedText] = Field(
        default=None,
        description="Extrahierter Text"
    )
    structured_data: Optional[StructuredData] = Field(
        default=None,
        description="Strukturierte Daten"
    )
    extraction_time: float = Field(description="Extraktionszeit in Sekunden")
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnungen während der Extraktion"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Fehler während der Extraktion"
    )
    # Neue Felder für asynchrone Verarbeitung
    job_id: Optional[str] = Field(
        default=None,
        description="Job-ID für asynchrone Verarbeitung"
    )
    processing_status: Optional[str] = Field(
        default=None,
        description="Verarbeitungsstatus"
    )


class AsyncExtractionRequest(BaseModel):
    """Request für asynchrone Extraktion."""
    
    callback_url: Optional[str] = Field(
        default=None,
        description="Callback-URL für Benachrichtigungen"
    )
    priority: str = Field(
        default="normal",
        description="Priorität (low, normal, high)"
    )
    retention_hours: int = Field(
        default=24,
        description="Aufbewahrungszeit in Stunden"
    )


class AsyncExtractionResponse(BaseModel):
    """Response für asynchrone Extraktion."""
    
    job_id: str = Field(description="Job-ID")
    status: str = Field(description="Status (queued, processing, completed, failed)")
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Geschätzte Fertigstellung"
    )
    progress: Optional[float] = Field(
        default=None,
        description="Fortschritt (0-100)"
    )
    result_url: Optional[str] = Field(
        default=None,
        description="URL zum Abrufen des Ergebnisses"
    )


class JobStatus(BaseModel):
    """Status eines asynchronen Jobs."""
    
    job_id: str = Field(description="Job-ID")
    status: str = Field(description="Status")
    created_at: datetime = Field(description="Erstellungszeit")
    started_at: Optional[datetime] = Field(
        default=None,
        description="Startzeit"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Fertigstellungszeit"
    )
    progress: float = Field(description="Fortschritt (0-100)")
    result: Optional[ExtractionResult] = Field(
        default=None,
        description="Extraktionsergebnis"
    )
    error: Optional[str] = Field(
        default=None,
        description="Fehlermeldung"
    )


class SupportedFormat(BaseModel):
    """Informationen über ein unterstütztes Dateiformat."""
    
    extension: str = Field(description="Dateiendung")
    mime_type: str = Field(description="MIME-Type")
    description: str = Field(description="Beschreibung des Formats")
    features: List[str] = Field(description="Unterstützte Features")
    max_size: Optional[int] = Field(
        default=None,
        description="Maximale Dateigröße in Bytes"
    )
    # Neue Felder
    category: str = Field(description="Kategorie (document, image, media, archive)")
    extraction_methods: List[str] = Field(
        default_factory=list,
        description="Verwendete Extraktionsmethoden"
    )


class FormatsResponse(BaseModel):
    """Response für unterstützte Formate."""
    
    formats: List[SupportedFormat] = Field(description="Liste unterstützter Formate")
    total_count: int = Field(description="Anzahl unterstützter Formate")
    categories: Dict[str, int] = Field(description="Anzahl pro Kategorie")


class HealthResponse(BaseModel):
    """Health-Check Response."""
    
    status: str = Field(description="Status der API")
    version: str = Field(description="API-Version")
    timestamp: datetime = Field(description="Zeitstempel")
    uptime: float = Field(description="Uptime in Sekunden")
    supported_formats_count: int = Field(description="Anzahl unterstützter Formate")
    # Neue Felder
    active_jobs: int = Field(description="Aktive Jobs")
    queue_size: int = Field(description="Warteschlangengröße")
    worker_status: str = Field(description="Worker-Status")


class ErrorResponse(BaseModel):
    """Standard-Fehler-Response."""
    
    error: str = Field(description="Fehlercode")
    message: str = Field(description="Fehlermeldung")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Zusätzliche Fehlerdetails"
    )
    timestamp: datetime = Field(description="Zeitstempel des Fehlers")
    job_id: Optional[str] = Field(
        default=None,
        description="Job-ID (bei asynchronen Fehlern)"
    )