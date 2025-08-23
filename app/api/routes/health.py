"""
Health-Check Routen für die API.
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.extractors import get_supported_formats
from app.models.schemas import HealthResponse

router = APIRouter()

# Startzeit für Uptime-Berechnung
_start_time = time.time()


@router.get(
    '/health',
    response_model=HealthResponse,
    summary='API-Status prüfen',
    description='Gibt den aktuellen Status der API zurück.',
)
async def health_check() -> HealthResponse:
    """
    Health-Check Endpoint für die API.

    Returns:
        HealthResponse mit API-Status und Informationen
    """
    try:
        # Unterstützte Formate zählen
        formats = get_supported_formats()
        total_formats = sum(len(f.get('extensions', [])) for f in formats)

        # Uptime berechnen
        uptime = time.time() - _start_time

        return HealthResponse(
            status='healthy',
            version=settings.app_version,
            timestamp=datetime.now(timezone.utc),
            uptime=uptime,
            supported_formats_count=total_formats,
        )
    except Exception:
        return HealthResponse(
            status='unhealthy',
            version=settings.app_version,
            timestamp=datetime.now(timezone.utc),
            uptime=time.time() - _start_time,
            supported_formats_count=0,
        )


@router.get(
    '/health/detailed',
    summary='Detaillierter API-Status',
    description='Gibt detaillierte Informationen über den API-Status zurück.',
)
async def detailed_health_check():
    """
    Detaillierter Health-Check mit zusätzlichen Informationen.

    Returns:
        Detaillierte Status-Informationen
    """
    try:
        # Basis-Health-Check
        basic_health = await health_check()

        # Zusätzliche Informationen
        formats = get_supported_formats()
        format_details = []

        for format_info in formats:
            format_details.append(
                {
                    'extractor': format_info.get('class'),
                    'extensions': format_info.get('extensions', []),
                    'mime_types': format_info.get('mime_types', []),
                    'max_file_size': format_info.get('max_file_size'),
                },
            )

        return {
            'basic_health': basic_health.dict(),
            'configuration': {
                'app_name': settings.app_name,
                'debug_mode': settings.debug,
                'max_file_size': settings.max_file_size,
                'extract_timeout': settings.extract_timeout,
                'allowed_extensions': settings.allowed_extensions,
            },
            'extractors': format_details,
            'system_info': {
                'python_version': '3.8+',
                'fastapi_version': '0.104.1+',
                'platform': 'linux',
            },
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        }


@router.get(
    '/health/ready',
    summary='Readiness-Check',
    description='Prüft, ob die API bereit ist, Anfragen zu verarbeiten.',
)
async def readiness_check():
    """
    Readiness-Check für Load Balancer und Container-Orchestration.

    Returns:
        Einfacher Status-Code
    """
    try:
        # Prüfe, ob Extraktoren verfügbar sind
        formats = get_supported_formats()
        if not formats:
            return {'status': 'not_ready', 'reason': 'No extractors available'}

        return {'status': 'ready'}

    except Exception as e:
        return {'status': 'not_ready', 'reason': str(e)}


@router.get(
    '/health/live',
    summary='Liveness-Check',
    description='Prüft, ob die API noch läuft.',
)
async def liveness_check():
    """
    Liveness-Check für Container-Orchestration.

    Returns:
        Einfacher Status-Code
    """
    return {
        'status': 'alive',
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    }
