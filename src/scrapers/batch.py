"""Batch scraper with rate limiting for efficient price collection."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any

from ..models import PriceSnapshot
from .selenium_base import SeleniumScraper

LOGGER = logging.getLogger(__name__)


@dataclass
class ScrapeTask:
    """Represents a single scraping task."""
    product_id: str
    product_name: str
    category: str
    store: str
    url: str
    desired_price: float


class BatchScraper:
    """
    Batch scraper with rate limiting and intelligent driver management.

    Features:
    - Groups tasks by store to avoid rate limiting
    - Adds delays between requests to same store
    - Uses shared driver for efficiency
    - Closes driver only after batch completion
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize batch scraper.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        scraping_config = config.get("scraping", {})
        self.rate_limit = scraping_config.get("rate_limit_per_store", 5)
        self.delay_seconds = scraping_config.get("delay_seconds", 2)

    async def scrape_batch(self, tasks: List[ScrapeTask]) -> List[PriceSnapshot]:
        """
        Execute scraping in batch with rate limiting.

        Processes all tasks efficiently while respecting rate limits per store.

        Args:
            tasks: List of scraping tasks

        Returns:
            List of price snapshots
        """
        if not tasks:
            return []

        LOGGER.info(f"Starting batch scrape of {len(tasks)} tasks")

        # Group by store to process sequentially per store
        by_store = defaultdict(list)
        for task in tasks:
            by_store[task.store].append(task)

        results = []

        # Process each store sequentially (avoid blocking)
        for store, store_tasks in by_store.items():
            LOGGER.info(f"Processing {len(store_tasks)} tasks for {store}")

            # Get scraper instance for this store
            scraper = self._get_scraper(store)
            if not scraper:
                LOGGER.warning(f"No scraper available for store: {store}")
                continue

            # Process tasks for this store with delays
            for i, task in enumerate(store_tasks):
                if i > 0:
                    # Add delay between requests to same store
                    await asyncio.sleep(self.delay_seconds)

                try:
                    # Fetch price (uses shared driver internally)
                    result = await asyncio.to_thread(scraper.fetch, task.url)

                    # Enrich with task metadata
                    result.product_id = task.product_id
                    result.product_name = task.product_name
                    result.category = task.category

                    results.append(result)

                    if result.price:
                        LOGGER.info(f"✅ {task.product_name} ({store}): R$ {result.price:.2f}")
                    else:
                        LOGGER.warning(f"⚠️ {task.product_name} ({store}): Price not found")

                except Exception as e:
                    LOGGER.error(f"❌ Error scraping {task.product_name} ({store}): {e}")

        # IMPORTANT: Close shared driver after batch completion
        SeleniumScraper.close_shared_driver()
        LOGGER.info(f"Batch scrape completed. {len(results)}/{len(tasks)} successful")

        return results

    def _get_scraper(self, store: str) -> SeleniumScraper:
        """
        Get scraper instance for store.

        Args:
            store: Store name

        Returns:
            Scraper instance or None if not found
        """
        # Import scrapers dynamically to avoid circular imports
        try:
            if store == "kabum":
                from .kabum import KabumScraper
                return KabumScraper()
            elif store == "amazon":
                from .amazon import AmazonScraper
                return AmazonScraper()
            elif store == "pichau":
                from .pichau import PichauScraper
                return PichauScraper()
            elif store == "terabyte":
                from .terabyte import TerabyteScraper
                return TerabyteScraper()
            elif store == "mercadolivre":
                from .mercadolivre import MercadolivreScraper
                return MercadolivreScraper()
            elif store == "inpower":
                from .inpower import InpowerScraper
                return InpowerScraper()
            else:
                LOGGER.warning(f"Unknown store: {store}")
                return None
        except ImportError as e:
            LOGGER.error(f"Failed to import scraper for {store}: {e}")
            return None


async def scrape_products_async(config: Dict[str, Any]) -> List[PriceSnapshot]:
    """
    Async helper to scrape all configured products.

    Args:
        config: Configuration dictionary

    Returns:
        List of price snapshots
    """
    products = config.get("products", [])
    enabled_products = [p for p in products if p.get("enabled", True)]

    # Build tasks
    tasks = []
    for product in enabled_products:
        product_id = product.get("id")
        product_name = product.get("name")
        category = product.get("category")
        desired_price = product.get("desired_price", 0)

        for url_data in product.get("urls", []):
            store = url_data.get("store")
            url = url_data.get("url")

            if store and url:
                task = ScrapeTask(
                    product_id=product_id,
                    product_name=product_name,
                    category=category,
                    store=store,
                    url=url,
                    desired_price=desired_price
                )
                tasks.append(task)

    # Execute batch scraping
    scraper = BatchScraper(config)
    return await scraper.scrape_batch(tasks)


def scrape_products_sync(config: Dict[str, Any]) -> List[PriceSnapshot]:
    """
    Synchronous wrapper for batch scraping.

    Args:
        config: Configuration dictionary

    Returns:
        List of price snapshots
    """
    return asyncio.run(scrape_products_async(config))
