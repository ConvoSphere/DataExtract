"""
Konfigurationsmanagement für die Universal File Extractor API.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Anwendungseinstellungen."""

    # API Konfiguration
    app_name: str = 'Universal File Content Extractor API'
    app_version: str = '0.1.0'
    debug: bool = Field(default=False, description='Debug-Modus aktivieren')

    # Server Konfiguration
    host: str = Field(default='0.0.0.0', description='Host für den Server')
    port: int = Field(default=8000, description='Port für den Server')

    # Datei-Konfiguration
    max_file_size: int = Field(
        default=150 * 1024 * 1024,  # 150MB
        description='Maximale Dateigröße in Bytes',
    )
    allowed_extensions: list[str] = Field(
        default=[
            # Dokumente
            '.pdf',
            '.docx',
            '.doc',
            '.rtf',
            '.odt',
            '.txt',
            # Tabellen
            '.xlsx',
            '.xls',
            '.ods',
            '.csv',
            # Präsentationen
            '.pptx',
            '.ppt',
            '.odp',
            # Datenformate
            '.json',
            '.xml',
            '.html',
            '.htm',
            '.yaml',
            '.yml',
            # Bilder
            '.jpg',
            '.jpeg',
            '.png',
            '.gif',
            '.bmp',
            '.tiff',
            '.tif',
            '.webp',
            '.svg',
            # Medien
            '.mp4',
            '.avi',
            '.mov',
            '.wmv',
            '.flv',
            '.webm',
            '.mp3',
            '.wav',
            '.flac',
            '.aac',
            '.ogg',
            # Archive
            '.zip',
            '.rar',
            '.7z',
            '.tar',
            '.gz',
        ],
        description='Erlaubte Dateiendungen',
    )

    # Extraktor-Konfiguration
    extract_timeout: int = Field(
        default=600,  # 10 Minuten
        description='Timeout für Extraktion in Sekunden',
    )

    # Parallelisierung
    max_concurrent_extractions: int = Field(
        default=10,
        description='Maximale Anzahl paralleler Extraktionen',
    )
    worker_processes: int = Field(
        default=4,
        description='Anzahl Worker-Prozesse für Extraktion',
    )

    # Pipeline-Konfiguration
    enable_async_processing: bool = Field(
        default=True,
        description='Asynchrone Verarbeitung aktivieren',
    )
    queue_size: int = Field(
        default=100,
        description='Größe der Verarbeitungswarteschlange',
    )
    batch_size: int = Field(
        default=5,
        description='Batch-Größe für parallele Verarbeitung',
    )

    # Speicher-Konfiguration
    temp_dir: str = Field(
        default='/tmp/file_extractor',
        description='Temporäres Verzeichnis für Dateiverarbeitung',
    )
    max_temp_files: int = Field(
        default=1000,
        description='Maximale Anzahl temporärer Dateien',
    )

    # Bild-Extraktion
    enable_image_extraction: bool = Field(
        default=True,
        description='Bild-Extraktion aktivieren',
    )
    image_max_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB pro Bild
        description='Maximale Bildgröße',
    )
    extract_image_text: bool = Field(
        default=True,
        description='OCR für Bilder aktivieren',
    )

    # Medien-Extraktion
    enable_media_extraction: bool = Field(
        default=True,
        description='Medien-Extraktion aktivieren',
    )
    media_max_duration: int = Field(
        default=300,  # 5 Minuten
        description='Maximale Mediendauer in Sekunden',
    )
    extract_audio_transcript: bool = Field(
        default=False,
        description='Audio-Transkription aktivieren',
    )

    # Docling-Konfiguration
    enable_docling: bool = Field(
        default=True,
        description='Docling für erweiterte Extraktion aktivieren',
    )
    enable_advanced_analysis: bool = Field(
        default=True,
        description='Erweiterte Analyse (Entitäten, Sentiment, Zusammenfassung) aktivieren',
    )
    docling_timeout: int = Field(
        default=300,  # 5 Minuten
        description='Timeout für Docling-Verarbeitung in Sekunden',
    )
    docling_cache_enabled: bool = Field(
        default=True,
        description='Docling-Cache aktivieren',
    )
    docling_cache_ttl: int = Field(
        default=3600,  # 1 Stunde
        description='Docling-Cache TTL in Sekunden',
    )

    # CORS Konfiguration
    cors_origins: list[str] = Field(
        default=['http://localhost:3000', 'http://localhost:8080'],
        description='Erlaubte CORS Origins (nicht * für Produktion)',
    )
    cors_allow_credentials: bool = Field(
        default=False,
        description='CORS Credentials erlauben',
    )
    cors_allow_methods: list[str] = Field(
        default=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        description='Erlaubte HTTP-Methoden für CORS',
    )
    cors_allow_headers: list[str] = Field(
        default=['*'],
        description='Erlaubte HTTP-Headers für CORS',
    )

    # Logging
    log_level: str = Field(default='INFO', description='Log-Level')

    # Sicherheit
    api_key_header: str = Field(
        default='X-API-Key',
        description='Header-Name für API-Key',
    )
    require_api_key: bool = Field(
        default=False,
        description='API-Key erforderlich',
    )

    # Redis-Konfiguration (für asynchrone Verarbeitung)
    redis_url: str = Field(
        default='redis://localhost:6379',
        description='Redis-URL für Job-Queue',
    )
    redis_db: int = Field(
        default=0,
        description='Redis-Datenbank',
    )

    # Cloud-Deployment
    environment: str = Field(
        default='development',
        description='Deployment-Umgebung',
    )
    enable_metrics: bool = Field(
        default=True,
        description='Metriken über OpenTelemetry aktivieren',
    )

    # Test/Dev: Verarbeitungslast simulieren (für Performance-Relationen)
    simulate_processing: bool = Field(
        default=True,
        description='Simuliert CPU-Last proportional zur Dateigröße (nicht in Produktion)',
    )

    # OpenTelemetry-Konfiguration
    enable_opentelemetry: bool = Field(
        default=True,
        description='OpenTelemetry aktivieren',
    )
    otlp_endpoint: str | None = Field(
        default=None,
        description='OTLP Endpoint für Tracing und Metriken (z.B. http://otel-collector:4317)',
    )
    otlp_headers: dict[str, str] = Field(
        default={},
        description='OTLP Headers für Authentifizierung',
    )
    enable_tracing: bool = Field(
        default=True,
        description='Distributed Tracing aktivieren',
    )

    # Logging-Konfiguration
    log_format: str = Field(
        default='json',
        description='Log-Format (json, console)',
    )
    enable_request_logging: bool = Field(
        default=True,
        description='Request-Logging aktivieren',
    )
    enable_extraction_logging: bool = Field(
        default=True,
        description='Extraktions-Logging aktivieren',
    )

    # Microservice-spezifische Konfiguration
    service_name: str = Field(
        default='file-extractor',
        description='Name des Microservices',
    )
    service_version: str = Field(
        default='0.1.0',
        description='Version des Microservices',
    )
    service_namespace: str = Field(
        default='file-extractor',
        description='Namespace für OpenTelemetry',
    )

    # Additional fields for .env compatibility
    secret_key: str = Field(
        default='your-secret-key-here', description='Secret key for the application',
    )
    allowed_hosts: str = Field(
        default='test,testserver,localhost,127.0.0.1', description='Allowed hosts',
    )
    celery_broker_url: str = Field(
        default='redis://redis:6379/0', description='Celery broker URL',
    )
    celery_result_backend: str = Field(
        default='redis://redis:6379/0', description='Celery result backend',
    )
    celery_task_serializer: str = Field(
        default='json', description='Celery task serializer',
    )
    celery_result_serializer: str = Field(
        default='json', description='Celery result serializer',
    )
    celery_accept_content: str = Field(
        default='json', description='Celery accept content',
    )
    celery_timezone: str = Field(default='UTC', description='Celery timezone')
    celery_enable_utc: str = Field(default='true', description='Celery enable UTC')
    jaeger_host: str = Field(default='jaeger', description='Jaeger host')
    jaeger_port: str = Field(default='6831', description='Jaeger port')
    prometheus_enabled: str = Field(default='true', description='Prometheus enabled')
    ocr_languages: str = Field(default='eng,deu', description='OCR languages')
    rate_limit_requests: str = Field(default='100', description='Rate limit requests')
    rate_limit_window: str = Field(default='60', description='Rate limit window')
    grafana_password: str = Field(default='admin', description='Grafana password')
    grafana_user: str = Field(default='admin', description='Grafana user')
    aws_region: str = Field(default='us-west-2', description='AWS region')
    smtp_port: str = Field(default='587', description='SMTP port')
    database_pool_size: str = Field(default='10', description='Database pool size')
    database_max_overflow: str = Field(
        default='20', description='Database max overflow',
    )

    class Config:
        env_file = '.env'
        case_sensitive = False


# Globale Settings-Instanz
settings = Settings()
