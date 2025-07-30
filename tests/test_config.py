"""Tests für die Konfiguration."""

from app.core.config import settings


def test_settings_loaded():
    """Testet, ob die Einstellungen korrekt geladen werden."""
    assert settings.app_name == 'Universal File Content Extractor API'
    assert settings.app_version == '0.1.0'
    assert settings.debug is False
    assert settings.max_file_size == 150 * 1024 * 1024  # 150MB


def test_docling_settings():
    """Testet die Docling-spezifischen Einstellungen."""
    assert settings.enable_docling is True
    assert settings.enable_advanced_analysis is True
    assert settings.docling_timeout == 300
    assert settings.docling_cache_enabled is True
    assert settings.docling_cache_ttl == 3600


def test_allowed_extensions():
    """Testet, ob erlaubte Erweiterungen definiert sind."""
    assert len(settings.allowed_extensions) > 0
    assert '.pdf' in settings.allowed_extensions
    assert '.txt' in settings.allowed_extensions
    assert '.json' in settings.allowed_extensions


def test_cors_settings():
    """Testet CORS-Einstellungen."""
    assert settings.cors_origins is not None
    assert '*' in settings.cors_origins or len(settings.cors_origins) > 0
