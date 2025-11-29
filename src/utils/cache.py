"""Price caching utilities."""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any

LOGGER = logging.getLogger(__name__)


class PriceCache:
    """
    Thread-safe singleton cache for storing price data.

    This cache stores prices with TTL (time-to-live) to avoid
    unnecessary scraping requests.
    """

    _instance: Optional["PriceCache"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache: Dict[str, Tuple[Any, datetime]] = {}
                    cls._instance._ttl = timedelta(minutes=30)
                    LOGGER.info("PriceCache initialized with TTL=30 minutes")
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if datetime.now() - timestamp < self._ttl:
                    LOGGER.debug(f"Cache hit: {key}")
                    return value
                else:
                    # Expired, remove from cache
                    del self._cache[key]
                    LOGGER.debug(f"Cache expired: {key}")

        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = (value, datetime.now())
            LOGGER.debug(f"Cache set: {key}")

    def clear_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = []

        with self._lock:
            for key, (_, timestamp) in self._cache.items():
                if now - timestamp >= self._ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        if expired_keys:
            LOGGER.info(f"Cleared {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def clear_all(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            LOGGER.info(f"Cleared all {count} cache entries")

    def set_ttl(self, minutes: int) -> None:
        """
        Set cache TTL.

        Args:
            minutes: TTL in minutes
        """
        with self._lock:
            self._ttl = timedelta(minutes=minutes)
            LOGGER.info(f"Cache TTL set to {minutes} minutes")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            now = datetime.now()
            total = len(self._cache)
            expired = sum(
                1
                for _, timestamp in self._cache.values()
                if now - timestamp >= self._ttl
            )
            active = total - expired

            return {
                "total_entries": total,
                "active_entries": active,
                "expired_entries": expired,
                "ttl_minutes": int(self._ttl.total_seconds() / 60),
            }

    def __len__(self) -> int:
        """Return number of cache entries."""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (even if expired)."""
        with self._lock:
            return key in self._cache
