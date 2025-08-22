"""
Security Middleware und Utilities.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('security')


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware für Security Headers und zusätzliche Sicherheitsmaßnahmen."""

    async def dispatch(self, request: Request, call_next):
        """Verarbeitet Request und fügt Security Headers hinzu."""

        # Request-Logging für Security
        self._log_security_request(request)

        # Security-Checks
        if not self._validate_request_security(request):
            return JSONResponse(
                status_code=400,
                content={'error': 'Security validation failed'},
            )

        # Response verarbeiten
        response = await call_next(request)

        # Security Headers hinzufügen
        self._add_security_headers(response)

        return response

    def _log_security_request(self, request: Request) -> None:
        """Loggt Security-relevante Request-Informationen."""
        logger.info(
            'Security request log',
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            content_length=request.headers.get('content-length'),
            content_type=request.headers.get('content-type'),
        )

    def _validate_request_security(self, request: Request) -> bool:
        """Validiert Request auf Security-Probleme."""

        # 1. Content-Length Check
        try:
            content_length = request.headers.get('content-length')
            if content_length is not None:
                size = int(content_length)
                if size > settings.max_file_size:
                    logger.warning('Request too large', size=size)
                    return False
        except ValueError:
            pass

        # 2. Content-Type Check für Uploads
        if request.method == 'POST' and '/extract' in str(request.url):
            content_type = request.headers.get('content-type', '')
            if not content_type.startswith('multipart/form-data'):
                logger.warning(
                    'Invalid content-type for upload',
                    content_type=content_type,
                )
                # Do not reject here; let route validation handle it
                return True

        # 3. User-Agent Check (optional)
        user_agent = request.headers.get('user-agent', '')
        if self._is_suspicious_user_agent(user_agent):
            logger.warning('Suspicious user agent', user_agent=user_agent)
            # Nicht ablehnen, nur loggen

        # 4. Rate Limiting Check (wird in auth.py gehandhabt)

        return True

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Prüft auf verdächtige User-Agents."""
        suspicious_patterns = [
            'bot',
            'crawler',
            'spider',
            'scraper',
            'curl',
            'wget',
            'python-requests',
            'sqlmap',
            'nikto',
            'nmap',
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)

    def _add_security_headers(self, response: Response) -> None:
        """Fügt Security Headers zur Response hinzu."""

        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # X-Frame-Options
        response.headers['X-Frame-Options'] = 'DENY'

        # X-Content-Type-Options
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Strict-Transport-Security (nur für HTTPS)
        if settings.environment == 'production':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=()'
        )

        # Cache Control für sensitive Endpoints
        try:
            if hasattr(response, 'url') and response.url:
                if '/health' in str(response.url) or '/metrics' in str(response.url):
                    response.headers['Cache-Control'] = (
                        'no-cache, no-store, must-revalidate'
                    )
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
        except (AttributeError, RuntimeError):
            # Ignore errors for responses without url attribute
            pass


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware für Input-Sanitization."""

    async def dispatch(self, request: Request, call_next):
        """Sanitized Request-Input."""

        # Response verarbeiten (Sanitizing-Ergebnisse aktuell nur intern genutzt)
        _ = self._sanitize_url(str(request.url))
        _ = self._sanitize_headers(dict(request.headers))
        return await call_next(request)

    def _sanitize_url(self, url: str) -> str:
        """Sanitized URL-Input."""
        # Entferne gefährliche Zeichen
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            url = url.replace(char, '')

        return url

    def _sanitize_headers(self, headers: dict) -> dict:
        """Sanitized Header-Input."""
        sanitized = {}

        for key, value in headers.items():
            # Entferne gefährliche Header
            if key.lower() in ['x-forwarded-for', 'x-real-ip', 'x-forwarded-host']:
                continue

            # Sanitize Header-Werte
            sanitized_value = self._sanitize_string(value)
            sanitized[key] = sanitized_value

        return sanitized

    def _sanitize_string(self, value: str) -> str:
        """Sanitized String-Input."""
        # Entferne gefährliche Zeichen
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')']
        for char in dangerous_chars:
            value = value.replace(char, '')

        return value


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware für Audit-Logging."""

    async def dispatch(self, request: Request, call_next):
        """Loggt Audit-Informationen."""

        # Audit-Log vor Request
        self._log_audit_request(request)

        # Response verarbeiten
        response = await call_next(request)

        # Audit-Log nach Response
        self._log_audit_response(request, response)

        return response

    def _log_audit_request(self, request: Request) -> None:
        """Loggt Audit-Informationen für Request."""
        logger.info(
            'Audit request',
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            timestamp=request.headers.get('x-request-id'),
        )

    def _log_audit_response(self, request: Request, response: Response) -> None:
        """Loggt Audit-Informationen für Response."""
        logger.info(
            'Audit response',
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            content_length=response.headers.get('content-length'),
            timestamp=request.headers.get('x-request-id'),
        )


def get_security_middleware() -> list:
    """Gibt die Security Middleware-Liste zurück."""
    return [
        SecurityHeadersMiddleware,
        InputSanitizationMiddleware,
        AuditLoggingMiddleware,
    ]
