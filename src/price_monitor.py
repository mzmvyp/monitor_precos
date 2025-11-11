from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from .config_loader import load_products_config
from .models import PriceSnapshot, ProductConfig, attach_target_price
from .scrapers import AmazonScraper, KabumScraper, MercadoLivreScraper
from .scrapers.terabyte import TerabyteScraper
from .scrapers.pichau import PichauScraper
from .scrapers.base import StoreScraper

LOGGER = logging.getLogger(__name__)

# Scrapers são criados de forma lazy para permitir configuração de SSL antes
_SCRAPERS_CACHE: dict[str, StoreScraper] | None = None


def get_scrapers() -> dict[str, StoreScraper]:
    """Retorna scrapers (criados sob demanda para respeitar config SSL)."""
    global _SCRAPERS_CACHE
    if _SCRAPERS_CACHE is None:
        _SCRAPERS_CACHE = {
            "kabum": KabumScraper(),
            "amazon": AmazonScraper(),
            "mercadolivre": MercadoLivreScraper(),
            "terabyte": TerabyteScraper(),
            "pichau": PichauScraper(),
        }
    return _SCRAPERS_CACHE


class PriceMonitor:
    def __init__(
        self,
        config_path: Path = Path("config/products.yaml"),
        history_path: Path = Path("data/price_history.csv"),
    ) -> None:
        self.config_path = config_path
        self.history_path = history_path
        self.products = load_products_config(config_path)

    def available_categories(self) -> set[str]:
        return {product.category for product in self.products.values()}

    def _ensure_history_file(self) -> None:
        if not self.history_path.parent.exists():
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_path.exists():
            df = pd.DataFrame(
                columns=[
                    "timestamp",
                    "product_id",
                    "product_name",
                    "category",
                    "store",
                    "url",
                    "price",
                    "currency",
                    "in_stock",
                    "raw_price",
                    "error",
                ]
            )
            df.to_csv(self.history_path, index=False, encoding="utf-8")

    def collect(self, product_ids: Sequence[str] | None = None) -> list[PriceSnapshot]:
        self._ensure_history_file()
        targets = product_ids or list(self.products.keys())

        snapshots: list[PriceSnapshot] = []
        for product_id in targets:
            product = self.products.get(product_id)
            if not product:
                LOGGER.warning("Produto %s não encontrado no config", product_id)
                continue

            for product_url in product.urls:
                scraper = get_scrapers().get(product_url.store)
                if not scraper:
                    LOGGER.warning("Loja %s não suportada ainda", product_url.store)
                    continue

                LOGGER.info("Coletando %s (%s)", product.name, product_url.store)
                snapshot = scraper.fetch(product_url.url)
                snapshots.append(
                    PriceSnapshot(
                        product_id=product.id,
                        product_name=product.name,
                        category=product.category,
                        store=snapshot.store,
                        url=product_url.url,
                        price=snapshot.price,
                        raw_price=snapshot.raw_price,
                        currency=snapshot.currency,
                        in_stock=snapshot.in_stock,
                        fetched_at=snapshot.fetched_at,
                        error=snapshot.error,
                    )
                )

        enriched = attach_target_price(snapshots, self.products)
        self._append_history(enriched)
        return enriched

    def _append_history(self, snapshots: Iterable[PriceSnapshot]) -> None:
        if not snapshots:
            return

        df = pd.DataFrame(
            [
                {
                    "timestamp": snap.fetched_at.isoformat(),
                    "product_id": snap.product_id,
                    "product_name": snap.product_name,
                    "category": snap.category,
                    "store": snap.store,
                    "url": snap.url,
                    "price": snap.price,
                    "currency": snap.currency,
                    "in_stock": snap.in_stock,
                    "raw_price": snap.raw_price,
                    "error": snap.error,
                }
                for snap in snapshots
            ]
        )
        df.to_csv(self.history_path, mode="a", header=not self.history_path.exists(), index=False, encoding="utf-8")

    def load_history(self) -> pd.DataFrame:
        self._ensure_history_file()
        return pd.read_csv(self.history_path, parse_dates=["timestamp"])

    def latest_by_product(self) -> dict[str, list[PriceSnapshot]]:
        history = self.load_history()
        latest_map: dict[str, list[PriceSnapshot]] = defaultdict(list)

        if history.empty:
            return latest_map

        history.sort_values("timestamp", inplace=True)
        for _, row in history.iterrows():
            snap = PriceSnapshot(
                product_id=row["product_id"],
                product_name=row["product_name"],
                category=row["category"],
                store=row["store"],
                url=row["url"],
                price=row["price"] if pd.notna(row["price"]) else None,
                raw_price=row.get("raw_price"),
                currency=row["currency"],
                in_stock=row["in_stock"] if pd.notna(row["in_stock"]) else None,
                fetched_at=row["timestamp"].to_pydatetime()
                if isinstance(row["timestamp"], pd.Timestamp)
                else datetime.fromisoformat(row["timestamp"]).astimezone(timezone.utc),
                error=row.get("error"),
            )
            latest_map[snap.product_id].append(snap)

        return latest_map

