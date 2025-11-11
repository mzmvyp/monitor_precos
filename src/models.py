from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional


@dataclass(slots=True)
class ProductURL:
    store: str
    url: str


@dataclass(slots=True)
class ProductConfig:
    id: str
    name: str
    category: str
    urls: list[ProductURL]
    desired_price: Optional[float] = None
    alternatives: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PriceSnapshot:
    product_id: str
    product_name: str
    category: str
    store: str
    url: str
    price: Optional[float]
    currency: str
    in_stock: Optional[bool]
    fetched_at: datetime
    raw_price: Optional[str] = None
    error: Optional[str] = None
    target_price: Optional[float] = field(default=None, repr=False, compare=False)

    @property
    def is_below_target(self) -> Optional[bool]:
        if self.price is None or self.target_price is None:
            return None
        return self.price <= self.target_price


def attach_target_price(
    snapshots: Iterable[PriceSnapshot], products: dict[str, ProductConfig]
) -> list[PriceSnapshot]:
    enriched: list[PriceSnapshot] = []
    for snapshot in snapshots:
        product_cfg = products.get(snapshot.product_id)
        target = product_cfg.desired_price if product_cfg else None
        snapshot.target_price = target
        enriched.append(snapshot)
    return enriched

