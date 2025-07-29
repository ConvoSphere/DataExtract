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
    language: Optional[str] = Field(
        default=None,
        description="Sprache für die Extraktion (ISO 639-1)"
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
    images: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Bild-Informationen"
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


class FormatsResponse(BaseModel):
    """Response für unterstützte Formate."""
    
    formats: List[SupportedFormat] = Field(description="Liste unterstützter Formate")
    total_count: int = Field(description="Anzahl unterstützter Formate")


class HealthResponse(BaseModel):
    """Health-Check Response."""
    
    status: str = Field(description="Status der API")
    version: str = Field(description="API-Version")
    timestamp: datetime = Field(description="Zeitstempel")
    uptime: float = Field(description="Uptime in Sekunden")
    supported_formats_count: int = Field(description="Anzahl unterstützter Formate")


class ErrorResponse(BaseModel):
    """Standard-Fehler-Response."""
    
    error: str = Field(description="Fehlercode")
    message: str = Field(description="Fehlermeldung")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Zusätzliche Fehlerdetails"
    )
    timestamp: datetime = Field(description="Zeitstempel des Fehlers")