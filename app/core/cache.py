"""
Caching-System für die Universal File Extractor API.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('cache')


class CacheManager:
    """Zentraler Cache-Manager für die Anwendung."""

    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
        }

        if REDIS_AVAILABLE and settings.redis_url:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    db=settings.redis_db,
                    decode_responses=True,
                )
                # Test-Verbindung
                self.redis_client.ping()
                logger.info('Redis cache initialized successfully')
            except Exception as e:
                logger.warning('Redis cache initialization failed', error=str(e))
                self.redis_client = None

    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generiert einen Cache-Schlüssel."""
        return f'{prefix}:{identifier}'

    def _generate_file_hash(self, file_path: Path) -> str:
        """Generiert einen Hash für eine Datei."""
        hasher = hashlib.sha256()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get(self, key: str) -> Any | None:
        """
        Holt einen Wert aus dem Cache.

        Args:
            key: Cache-Schlüssel

        Returns:
            Gecachter Wert oder None
        """
        try:
            # Redis-Cache versuchen
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    logger.debug('Cache hit (Redis)', key=key)
                    return json.loads(value)

            # Memory-Cache versuchen
            if key in self.memory_cache:
                cache_entry = self.memory_cache[key]
                if cache_entry['expires_at'] > datetime.now(UTC):
                    self.cache_stats['hits'] += 1
                    logger.debug('Cache hit (Memory)', key=key)
                    return cache_entry['value']
                # Abgelaufener Eintrag entfernen
                del self.memory_cache[key]

            self.cache_stats['misses'] += 1
            logger.debug('Cache miss', key=key)
            return None

        except (OSError, ValueError, TypeError) as e:
            logger.error('Cache get error', error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Speichert einen Wert im Cache.

        Args:
            key: Cache-Schlüssel
            value: Zu cachender Wert
            ttl: Time-to-live in Sekunden

        Returns:
            True wenn erfolgreich
        """
        try:
            # Redis-Cache versuchen
            if self.redis_client:
                success = self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str),
                )
                if success:
                    self.cache_stats['sets'] += 1
                    logger.debug('Cache set (Redis)', key=key, ttl=ttl)
                    return True

            # Memory-Cache als Fallback
            expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
            self.memory_cache[key] = {
                'value': value,
                'expires_at': expires_at,
            }
            self.cache_stats['sets'] += 1
            logger.debug('Cache set (Memory)', key=key, ttl=ttl)
            return True

        except (OSError, ValueError, TypeError) as e:
            logger.error('Cache set error', error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """
        Löscht einen Wert aus dem Cache.

        Args:
            key: Cache-Schlüssel

        Returns:
            True wenn erfolgreich
        """
        try:
            # Redis-Cache
            if self.redis_client:
                self.redis_client.delete(key)

            # Memory-Cache
            if key in self.memory_cache:
                del self.memory_cache[key]

            self.cache_stats['deletes'] += 1
            logger.debug('Cache delete', key=key)
            return True

        except (OSError, ValueError, TypeError) as e:
            logger.error('Cache delete error', error=str(e))
            return False

    def clear(self) -> bool:
        """
        Löscht den gesamten Cache.

        Returns:
            True wenn erfolgreich
        """
        try:
            # Redis-Cache
            if self.redis_client:
                self.redis_client.flushdb()

            # Memory-Cache
            self.memory_cache.clear()

            logger.info('Cache cleared')
            return True

        except (OSError, ValueError, TypeError) as e:
            logger.error('Cache clear error', error=str(e))
            return False

    def get_stats(self) -> dict[str, Any]:
        """Gibt Cache-Statistiken zurück."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (
            (self.cache_stats['hits'] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'hit_rate': round(hit_rate, 2),
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None,
        }

    def cache_extraction_result(self, file_path: Path, result: dict[str, Any]) -> bool:
        """
        Cached ein Extraktionsergebnis.

        Args:
            file_path: Pfad zur Datei
            result: Extraktionsergebnis

        Returns:
            True wenn erfolgreich
        """
        if not settings.docling_cache_enabled:
            return False

        try:
            # Cache-Schlüssel basierend auf Datei-Hash
            file_hash = self._generate_file_hash(file_path)
            cache_key = self._generate_key('extraction', file_hash)

            # TTL aus Konfiguration
            ttl = settings.docling_cache_ttl

            return self.set(cache_key, result, ttl)

        except (OSError, ValueError, TypeError) as e:
            logger.error('Cache extraction result error', error=str(e))
            return False

    def get_cached_extraction(self, file_path: Path) -> dict[str, Any] | None:
        """
        Holt ein gecachtes Extraktionsergebnis.

        Args:
            file_path: Pfad zur Datei

        Returns:
            Gecachtes Ergebnis oder None
        """
        if not settings.docling_cache_enabled:
            return None

        try:
            # Cache-Schlüssel basierend auf Datei-Hash
            file_hash = self._generate_file_hash(file_path)
            cache_key = self._generate_key('extraction', file_hash)

            return self.get(cache_key)

        except (OSError, ValueError, TypeError) as e:
            logger.error('Get cached extraction error', error=str(e))
            return None

    def invalidate_file_cache(self, file_path: Path) -> bool:
        """
        Invalidiert den Cache für eine spezifische Datei.

        Args:
            file_path: Pfad zur Datei

        Returns:
            True wenn erfolgreich
        """
        try:
            file_hash = self._generate_file_hash(file_path)
            cache_key = self._generate_key('extraction', file_hash)

            return self.delete(cache_key)

        except (OSError, ValueError, TypeError) as e:
            logger.error('Invalidate file cache error', error=str(e))
            return False


# Globale Cache-Instanz
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Gibt die globale Cache-Instanz zurück."""
    return cache_manager


# Convenience-Funktionen
def cache_get(key: str) -> Any | None:
    """Holt einen Wert aus dem Cache."""
    return cache_manager.get(key)


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Speichert einen Wert im Cache."""
    return cache_manager.set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """Löscht einen Wert aus dem Cache."""
    return cache_manager.delete(key)


def cache_clear() -> bool:
    """Löscht den gesamten Cache."""
    return cache_manager.clear()


def cache_stats() -> dict[str, Any]:
    """Gibt Cache-Statistiken zurück."""
    return cache_manager.get_stats()
