"""Tests for price cache utilities."""

import time
import pytest
from src.utils.cache import PriceCache


@pytest.fixture
def cache():
    """Create fresh cache instance for each test."""
    # Clear any existing cache
    cache_instance = PriceCache()
    cache_instance.clear_all()
    cache_instance.set_ttl(1)  # Short TTL for testing (1 minute)
    return cache_instance


class TestPriceCache:
    """Test PriceCache functionality."""

    def test_singleton_pattern(self):
        """Test that PriceCache is a singleton"""
        cache1 = PriceCache()
        cache2 = PriceCache()
        assert cache1 is cache2

    def test_set_and_get(self, cache):
        """Test setting and getting values"""
        cache.set("test_key", 123.45)
        assert cache.get("test_key") == 123.45

    def test_get_nonexistent_key(self, cache):
        """Test getting non-existent key returns None"""
        assert cache.get("nonexistent") is None

    def test_get_expired_value(self, cache):
        """Test that expired values return None"""
        cache.set_ttl(0)  # TTL = 0 minutes (instant expiry)
        cache.set("test_key", 123.45)
        time.sleep(0.1)  # Wait a bit
        assert cache.get("test_key") is None

    def test_overwrite_value(self, cache):
        """Test overwriting existing value"""
        cache.set("test_key", 100.0)
        cache.set("test_key", 200.0)
        assert cache.get("test_key") == 200.0

    def test_clear_expired(self, cache):
        """Test clearing expired entries"""
        cache.set_ttl(0)  # Instant expiry
        cache.set("expired1", 100.0)
        cache.set("expired2", 200.0)
        time.sleep(0.1)

        # Add fresh entry
        cache.set_ttl(60)
        cache.set("fresh", 300.0)

        cleared = cache.clear_expired()
        assert cleared == 2  # Should clear 2 expired entries
        assert cache.get("fresh") == 300.0
        assert cache.get("expired1") is None

    def test_clear_all(self, cache):
        """Test clearing all entries"""
        cache.set("key1", 100.0)
        cache.set("key2", 200.0)
        cache.set("key3", 300.0)

        cache.clear_all()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        assert len(cache) == 0

    def test_cache_length(self, cache):
        """Test cache length"""
        assert len(cache) == 0

        cache.set("key1", 100.0)
        assert len(cache) == 1

        cache.set("key2", 200.0)
        assert len(cache) == 2

        cache.clear_all()
        assert len(cache) == 0

    def test_cache_contains(self, cache):
        """Test __contains__ method"""
        cache.set("test_key", 123.45)
        assert "test_key" in cache
        assert "nonexistent" not in cache

    def test_get_stats(self, cache):
        """Test cache statistics"""
        cache.set_ttl(60)
        cache.set("key1", 100.0)
        cache.set("key2", 200.0)

        stats = cache.get_stats()

        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["ttl_minutes"] == 60

    def test_different_data_types(self, cache):
        """Test caching different data types"""
        cache.set("float", 123.45)
        cache.set("int", 100)
        cache.set("string", "test")
        cache.set("dict", {"a": 1, "b": 2})
        cache.set("list", [1, 2, 3])

        assert cache.get("float") == 123.45
        assert cache.get("int") == 100
        assert cache.get("string") == "test"
        assert cache.get("dict") == {"a": 1, "b": 2}
        assert cache.get("list") == [1, 2, 3]
