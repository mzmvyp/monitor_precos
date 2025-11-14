from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from .alert_manager import AlertManager
from .config_loader import load_products_config
from .models import PriceSnapshot, ProductConfig, attach_target_price
from .scrapers import AmazonScraper, KabumScraper, MercadoLivreScraper, RoyalCaribbeanScraper
from .scrapers.terabyte import TerabyteScraper
from .scrapers.pichau import PichauScraper
from .scrapers.base import StoreScraper
from .price_cache import PriceCacheManager

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
            "royalcaribbean": RoyalCaribbeanScraper(),
        }
    return _SCRAPERS_CACHE


class PriceMonitor:
    def __init__(
        self,
        config_path: Path = Path("config/products.yaml"),
        history_path: Path = Path("data/price_history.csv"),
        enable_alerts: bool = True,
        enable_cache: bool = True,
    ) -> None:
        self.config_path = config_path
        self.history_path = history_path
        self.products = load_products_config(config_path)
        self.alert_manager = AlertManager() if enable_alerts else None
        self.cache = PriceCacheManager() if enable_cache else None

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

    def collect(self, product_ids: Sequence[str] | None = None, max_retries: int = 3) -> list[PriceSnapshot]:
        """Coleta preços com retry automático para lojas problemáticas."""
        self._ensure_history_file()
        targets = product_ids or list(self.products.keys())

        snapshots: list[PriceSnapshot] = []
        failed_stores: dict[str, int] = {}  # store -> tentativas
        
        for product_id in targets:
            product = self.products.get(product_id)
            if not product:
                LOGGER.warning("Produto %s não encontrado no config", product_id)
                continue

            for product_url in product.urls:
                store = product_url.store
                
                # Verificar cache primeiro
                if self.cache:
                    cached = self.cache.get(product.id, store, product_url.url)
                    if cached:
                        LOGGER.info("Usando preço do cache: %s (%s) - R$ %.2f", 
                                  product.name, store, cached.price)
                        snapshots.append(
                            PriceSnapshot(
                                product_id=product.id,
                                product_name=product.name,
                                category=product.category,
                                store=store,
                                url=product_url.url,
                                price=cached.price,
                                raw_price=cached.raw_price,
                                currency="BRL",
                                in_stock=None,
                                fetched_at=datetime.now(timezone.utc),
                                error=None,
                                metadata={},
                            )
                        )
                        continue
                
                # Retry para lojas problemáticas
                for attempt in range(max_retries):
                    scraper = get_scrapers().get(store)
                    if not scraper:
                        LOGGER.warning("Loja %s não suportada ainda", store)
                        break

                    LOGGER.info("Coletando %s (%s) - Tentativa %d/%d", product.name, store, attempt + 1, max_retries)
                    
                    try:
                        snapshot = scraper.fetch(product_url.url)
                        
                        # Armazenar no cache se sucesso
                        if self.cache and snapshot.price and not snapshot.error:
                            self.cache.set(
                                product.id, store, product_url.url,
                                snapshot.price, snapshot.raw_price
                            )
                        
                        # Se teve erro, tentar novamente
                        if snapshot.error and attempt < max_retries - 1:
                            failed_stores[store] = failed_stores.get(store, 0) + 1
                            wait_time = 30 * (attempt + 1)  # Delay progressivo
                            LOGGER.warning("Erro ao coletar %s (%s), aguardando %ds antes de retry...", 
                                         product.name, store, wait_time)
                            import time
                            time.sleep(wait_time)
                            continue
                        
                        new_snapshot = PriceSnapshot(
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
                            metadata=snapshot.metadata,
                        )
                        snapshots.append(new_snapshot)

                        # Verificar se há Open Box disponível
                        if (self.alert_manager and
                            snapshot.metadata.get("has_open_box") and
                            snapshot.price):
                            open_box_url = snapshot.metadata.get("open_box_url")
                            open_box_price = snapshot.metadata.get("open_box_price")

                            if open_box_url:
                                self.alert_manager.alert_open_box(
                                    product_id=product.id,
                                    product_name=product.name,
                                    store=snapshot.store,
                                    product_url=product_url.url,
                                    open_box_url=open_box_url,
                                    regular_price=snapshot.price,
                                    open_box_price=open_box_price,
                                )
                        break  # Sucesso, sair do loop de retry
                        
                    except Exception as e:
                        if attempt < max_retries - 1:
                            failed_stores[store] = failed_stores.get(store, 0) + 1
                            wait_time = 30 * (attempt + 1)
                            LOGGER.warning("Exceção ao coletar %s (%s): %s. Aguardando %ds...", 
                                         product.name, store, e, wait_time)
                            import time
                            time.sleep(wait_time)
                        else:
                            # Última tentativa falhou
                            snapshots.append(
                                PriceSnapshot(
                                    product_id=product.id,
                                    product_name=product.name,
                                    category=product.category,
                                    store=store,
                                    url=product_url.url,
                                    price=None,
                                    raw_price=None,
                                    currency="BRL",
                                    in_stock=None,
                                    fetched_at=datetime.now(timezone.utc),
                                    error=str(e),
                                    metadata={},
                                )
                            )

        if failed_stores:
            LOGGER.info(f"Lojas com falhas (após retries): {failed_stores}")

        enriched = attach_target_price(snapshots, self.products)
        self._append_history(enriched)
        
        # Verificar alertas
        if self.alert_manager:
            self._check_alerts(enriched)
        
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
    
    def _check_alerts(self, snapshots: Iterable[PriceSnapshot]) -> None:
        """Verifica e envia alertas para os snapshots."""
        if not self.alert_manager:
            return
        
        # Carregar histórico para comparar preços
        history = self.load_history()
        
        for snap in snapshots:
            if not snap.price or snap.error:
                continue
            
            # Buscar preço anterior
            product_history = history[
                (history["product_id"] == snap.product_id) &
                (history["store"] == snap.store) &
                (history["price"].notna())
            ].sort_values("timestamp")
            
            if len(product_history) < 2:
                continue  # Precisa de pelo menos 2 registros para comparar
            
            previous_price = product_history.iloc[-2]["price"]
            
            # Obter preço desejado do produto
            product = self.products.get(snap.product_id)
            desired_price = product.desired_price if product else None
            
            # Verificar e enviar alerta
            self.alert_manager.check_and_alert(
                product_id=snap.product_id,
                product_name=snap.product_name,
                store=snap.store,
                url=snap.url,
                current_price=snap.price,
                previous_price=previous_price,
                desired_price=desired_price,
            )

