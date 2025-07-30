"""
Authentifizierung für die Universal File Extractor API.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("auth")

# Security scheme für API-Key
security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API-Key Authentifizierung."""

    def __init__(self):
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> dict[str, dict]:
        """Lädt API-Keys aus der Konfiguration."""
        # In Produktion sollten diese aus einer sicheren Quelle geladen werden
        # z.B. Datenbank, Vault, etc.
        return {
            "test-key-123": {
                "name": "Test User",
                "permissions": ["read", "write"],
                "rate_limit": 100,
            },
            "admin-key-456": {
                "name": "Admin User",
                "permissions": ["read", "write", "admin"],
                "rate_limit": 1000,
            },
        }

    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validiert einen API-Key."""
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        return None

    def has_permission(self, api_key: str, permission: str) -> bool:
        """Prüft, ob ein API-Key eine bestimmte Berechtigung hat."""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return False
        return permission in key_info.get("permissions", [])

    def get_rate_limit(self, api_key: str) -> int:
        """Gibt das Rate-Limit für einen API-Key zurück."""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return 10  # Default Rate-Limit
        return key_info.get("rate_limit", 10)


# Globale Auth-Instanz
auth = APIKeyAuth()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
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
            "name": "anonymous",
            "permissions": ["read"],
            "rate_limit": 10,
        }

    if not credentials:
        logger.warning("API key missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = credentials.credentials
    user_info = auth.validate_api_key(api_key)

    if not user_info:
        logger.warning("Invalid API key", api_key=api_key[:8] + "...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("API key validated", user=user_info["name"])
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
        if permission not in user.get("permissions", []):
            logger.warning(
                "Permission denied",
                user=user.get("name"),
                required_permission=permission,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return user

    return _require_permission


# Convenience-Dependencies
require_read = require_permission("read")
require_write = require_permission("write")
require_admin = require_permission("admin")


class RateLimiter:
    """Rate-Limiting für API-Requests."""
    
    def __init__(self):
        self.requests = {}  # In Produktion Redis verwenden

    def check_rate_limit(self, api_key: str, user_info: dict) -> bool:
        """
        Prüft das Rate-Limit für einen API-Key.
        
        Args:
            api_key: API-Key
            user_info: User-Informationen
            
        Returns:
            True, wenn Rate-Limit nicht überschritten
        """
        # Einfache In-Memory-Implementierung
        # In Produktion sollte Redis verwendet werden
        import time
        
        current_time = time.time()
        rate_limit = user_info.get("rate_limit", 10)
        
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # Alte Requests entfernen (1-Minuten-Fenster)
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if current_time - req_time < 60
        ]
        
        # Rate-Limit prüfen
        if len(self.requests[api_key]) >= rate_limit:
            logger.warning(
                "Rate limit exceeded",
                api_key=api_key[:8] + "...",
                rate_limit=rate_limit,
            )
            return False
        
        # Request hinzufügen
        self.requests[api_key].append(current_time)
        return True


# Globale Rate-Limiter-Instanz
rate_limiter = RateLimiter()


async def check_rate_limit(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency für Rate-Limiting.
    
    Args:
        user: User-Informationen
        
    Returns:
        User-Informationen
        
    Raises:
        HTTPException: Wenn Rate-Limit überschritten
    """
    # API-Key aus dem Request extrahieren
    # In einer echten Implementierung würde dies aus dem Request-Kontext kommen
    api_key = "dummy-key"  # Placeholder
    
    if not rate_limiter.check_rate_limit(api_key, user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    
    return user