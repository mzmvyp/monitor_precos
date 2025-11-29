"""Cache de preços para evitar requests desnecessários."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class PriceCache:
    """Cache temporário para evitar requests desnecessários."""
    product_id: str
    store: str
    url: str
    price: float
    raw_price: Optional[str]
    cached_at: datetime
    ttl_minutes: int = 30
    
    def is_valid(self) -> bool:
        """Verifica se o cache ainda é válido."""
        age = datetime.now(timezone.utc) - self.cached_at
        return age.total_seconds() < (self.ttl_minutes * 60)


class PriceCacheManager:
    """Gerencia cache de preços."""
    
    def __init__(self):
        self._cache: dict[str, PriceCache] = {}
    
    def _make_key(self, product_id: str, store: str, url: str) -> str:
        """Cria chave única para o cache."""
        return f"{product_id}:{store}:{url}"
    
    def get(self, product_id: str, store: str, url: str) -> Optional[PriceCache]:
        """Obtém preço do cache se válido."""
        key = self._make_key(product_id, store, url)
        cached = self._cache.get(key)
        
        if cached and cached.is_valid():
            LOGGER.debug(f"Cache HIT: {product_id} ({store})")
            return cached
        
        if cached:
            LOGGER.debug(f"Cache EXPIRADO: {product_id} ({store})")
            del self._cache[key]
        
        return None
    
    def set(self, product_id: str, store: str, url: str, price: float, 
            raw_price: Optional[str] = None, ttl_minutes: int = 30) -> None:
        """Armazena preço no cache."""
        key = self._make_key(product_id, store, url)
        self._cache[key] = PriceCache(
            product_id=product_id,
            store=store,
            url=url,
            price=price,
            raw_price=raw_price,
            cached_at=datetime.now(timezone.utc),
            ttl_minutes=ttl_minutes,
        )
        LOGGER.debug(f"Cache SET: {product_id} ({store}) - R$ {price}")
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()
        LOGGER.info("Cache limpo")
    
    def clear_expired(self) -> None:
        """Remove entradas expiradas do cache."""
        expired_keys = [
            key for key, cached in self._cache.items()
            if not cached.is_valid()
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            LOGGER.debug(f"Removidas {len(expired_keys)} entradas expiradas do cache")

