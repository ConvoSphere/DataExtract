"""
Konfigurationsmanagement für die Universal File Extractor API.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Anwendungseinstellungen."""
    
    # API Konfiguration
    app_name: str = "Universal File Content Extractor API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug-Modus aktivieren")
    
    # Server Konfiguration
    host: str = Field(default="0.0.0.0", description="Host für den Server")
    port: int = Field(default=8000, description="Port für den Server")
    
    # Datei-Konfiguration
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximale Dateigröße in Bytes"
    )
    allowed_extensions: List[str] = Field(
        default=[
            ".pdf", ".docx", ".doc", ".txt", ".csv", 
            ".json", ".xml", ".xlsx", ".xls", ".rtf",
            ".odt", ".ods", ".odp", ".html", ".htm"
        ],
        description="Erlaubte Dateiendungen"
    )
    
    # Extraktor-Konfiguration
    extract_timeout: int = Field(
        default=300,  # 5 Minuten
        description="Timeout für Extraktion in Sekunden"
    )
    
    # CORS Konfiguration
    cors_origins: List[str] = Field(
        default=["*"],
        description="Erlaubte CORS Origins"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Log-Level")
    
    # Sicherheit
    api_key_header: str = Field(
        default="X-API-Key",
        description="Header-Name für API-Key"
    )
    require_api_key: bool = Field(
        default=False,
        description="API-Key erforderlich"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Globale Settings-Instanz
settings = Settings()