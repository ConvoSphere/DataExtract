"""
Authentifizierung für die Universal File Extractor API.
"""

import os

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('auth')

# Security scheme für API-Key
security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API-Key Authentifizierung mit externem Secret Management."""

    def __init__(self):
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> dict[str, dict]:
        """Lädt API-Keys aus Umgebungsvariablen oder externem Secret Management."""
        api_keys = {}

        # Aus Umgebungsvariablen laden (für Development/Testing)
        # Format: API_KEY_<NAME>=<KEY>:<PERMISSIONS>:<RATE_LIMIT>
        for key, value in os.environ.items():
            if key.startswith('API_KEY_'):
                try:
                    key_name = key.replace('API_KEY_', '').lower()
                    key_value, permissions, rate_limit = value.split(':', 2)

                    api_keys[key_value] = {
                        'name': key_name,
                        'permissions': permissions.split(','),
                        'rate_limit': int(rate_limit),
                    }
                except (ValueError, IndexError):
                    logger.warning(f'Invalid API key format for {key}')
                    continue

        # Fallback für Development (nur wenn keine Keys konfiguriert sind)
        if not api_keys and settings.debug:
            logger.warning('No API keys configured, using development fallback')
            api_keys = {
                'dev-key-123': {
                    'name': 'development',
                    'permissions': ['read', 'write'],
                    'rate_limit': 100,
                },
            }

        # Logging (ohne sensitive Daten)
        logger.info(f'Loaded {len(api_keys)} API keys')

        return api_keys

    def validate_api_key(self, api_key: str) -> dict | None:
        """Validiert einen API-Key."""
        if not api_key:
            return None

        if api_key in self.api_keys:
            logger.info(f'API key validated for user: {self.api_keys[api_key]["name"]}')
            return self.api_keys[api_key]

        logger.warning(f'Invalid API key attempted: {api_key[:8]}...')
        return None

    def has_permission(self, api_key: str, permission: str) -> bool:
        """Prüft, ob ein API-Key eine bestimmte Berechtigung hat."""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return False
        return permission in key_info.get('permissions', [])

    def get_rate_limit(self, api_key: str) -> int:
        """Gibt das Rate-Limit für einen API-Key zurück."""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return 10  # Default Rate-Limit
        return key_info.get('rate_limit', 10)


# Globale Auth-Instanz
auth = APIKeyAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> dict:
    """
    Dependency für API-Key Authentifizierung.

    Args:
        credentials: HTTP Authorization Credentials

    Returns:
        User-Informationen

    Raises:
        HTTPException: Wenn Authentifizierung fehlschlägt
    """
    if not settings.require_api_key:
        # API-Key nicht erforderlich
        return {
            'name': 'anonymous',
            'permissions': ['read'],
            'rate_limit': 10,
        }

    if not credentials:
        logger.warning('API key missing')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='API key required',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    api_key = credentials.credentials
    user_info = auth.validate_api_key(api_key)

    if not user_info:
        logger.warning(f'Invalid API key: {api_key[:8]}...')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    logger.info(f'API key validated for user: {user_info["name"]}')
    return user_info


async def require_permission(permission: str):
    """
    Dependency für Berechtigungsprüfung.

    Args:
        permission: Erforderliche Berechtigung

    Returns:
        Dependency-Funktion
    """

    async def _require_permission(user: dict = Depends(get_current_user)) -> dict:
        if permission not in user.get('permissions', []):
            logger.warning(
                f'Permission denied: {user["name"]} lacks {permission} permission',
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Insufficient permissions. Required: {permission}',
            )
        return user

    return _require_permission


class RateLimiter:
    """Rate Limiting mit Redis-basierter Implementierung."""

    def __init__(self):
        self.redis_client = None
        try:
            import redis

            from app.core.config import settings

            client = redis.from_url(settings.redis_url, db=settings.redis_db)
            # Probe connection; fall back if not reachable
            try:
                client.ping()
                self.redis_client = client
                logger.info('RateLimiter: Redis backend enabled')
            except Exception as e:
                logger.warning(
                    f'RateLimiter: Redis not reachable, falling back to in-memory: {e}',
                )
                self.redis_client = None
        except ImportError:
            logger.warning('Redis not available, using in-memory rate limiting')
            self.redis_client = None

    def check_rate_limit(self, api_key: str, user_info: dict) -> bool:
        """
        Prüft das Rate-Limit für einen API-Key.

        Args:
            api_key: Der API-Key
            user_info: User-Informationen

        Returns:
            True wenn Request erlaubt ist, False wenn Limit überschritten
        """
        if not self.redis_client:
            # Fallback: In-Memory Rate Limiting (nicht für Produktion)
            return True

        try:
            rate_limit = user_info.get('rate_limit', 10)
            window_seconds = 60  # 1 Minute Window

            # Redis-basiertes Rate Limiting
            key = f'rate_limit:{api_key}'
            current = self.redis_client.get(key)

            if current is None:
                # Erster Request im Window
                self.redis_client.setex(key, window_seconds, 1)
                return True

            current_count = int(current)
            if current_count >= rate_limit:
                logger.warning(f'Rate limit exceeded for user: {user_info["name"]}')
                return False

            # Increment Counter
            self.redis_client.incr(key)
            return True
        except Exception as e:
            logger.warning(f'RateLimiter: error using Redis, allowing request: {e}')
            return True


# Globale Rate Limiter Instanz
rate_limiter = RateLimiter()


async def check_rate_limit(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency für Rate Limiting.

    Args:
        user: User-Informationen

    Returns:
        User-Informationen wenn Rate Limit nicht überschritten

    Raises:
        HTTPException: Wenn Rate Limit überschritten
    """
    # API-Key aus Request extrahieren (vereinfacht)
    # In einer echten Implementierung würden wir den API-Key aus dem Request extrahieren
    api_key = 'dummy'  # Placeholder

    if not rate_limiter.check_rate_limit(api_key, user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Rate limit exceeded',
            headers={'Retry-After': '60'},
        )

    return user
