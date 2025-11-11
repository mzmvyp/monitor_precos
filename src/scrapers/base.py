from __future__ import annotations

import abc
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import PriceSnapshot

LOGGER = logging.getLogger(__name__)


PRICE_PATTERN = re.compile(r"R\$\s*([0-9\.\s]+,[0-9]{2})")


def parse_brazilian_currency(value: str) -> Optional[float]:
    match = PRICE_PATTERN.search(value)
    if not match:
        return None
    number = match.group(1)
    digits = number.replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(digits)
    except ValueError:
        LOGGER.debug("Falha ao converter preço: %s", number)
        return None


@dataclass(slots=True)
class ScraperContext:
    store: str
    url: str


class StoreScraper(abc.ABC):
    store: str
    currency: str = "BRL"

    def __init__(self) -> None:
        self.verify = self._resolve_ssl_verification()
        
        # Desabilitar warnings SSL se necessário
        if self.verify is False:
            try:
                from urllib3 import disable_warnings
                from urllib3.exceptions import InsecureRequestWarning
                disable_warnings(InsecureRequestWarning)
            except Exception:  # noqa: BLE001
                LOGGER.debug("Não foi possível desabilitar avisos do urllib3.")
        
        self.session = self._create_session()
        self.session.verify = self.verify
        proxies = self._resolve_proxies()
        if proxies:
            self.session.proxies.update(proxies)

    @staticmethod
    def _create_session():
        import requests

        session = requests.Session()
        session.headers.update(
            {
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                ),
                "accept-language": "pt-BR,pt;q=0.9,en;q=0.8",
            }
        )
        return session

    @staticmethod
    def _resolve_ssl_verification():
        env_value = os.getenv("SCRAPER_VERIFY_SSL")
        ca_bundle = os.getenv("SCRAPER_CA_BUNDLE")
        if ca_bundle:
            return ca_bundle
        if env_value is None:
            return True
        return env_value.strip().lower() not in {"0", "false", "no"}

    @staticmethod
    def _resolve_proxies():
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        proxies = {}
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy
        return proxies

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def fetch(self, url: str) -> PriceSnapshot:
        ctx = ScraperContext(store=self.store, url=url)
        try:
            html = self._get_html(ctx)
            price, raw_price, metadata = self._parse(ctx, html)
            return PriceSnapshot(
                product_id="",
                product_name="",
                category="",
                store=self.store,
                url=url,
                price=price,
                raw_price=raw_price,
                currency=self.currency,
                in_stock=metadata.get("in_stock"),
                fetched_at=datetime.now(timezone.utc),
                error=None,
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Erro ao coletar %s (%s)", url, self.store)
            return PriceSnapshot(
                product_id="",
                product_name="",
                category="",
                store=self.store,
                url=url,
                price=None,
                raw_price=None,
                currency=self.currency,
                in_stock=None,
                fetched_at=datetime.now(timezone.utc),
                error=str(exc),
            )

    def _get_html(self, ctx: ScraperContext) -> str:
        response = self.session.get(ctx.url, timeout=20)
        response.raise_for_status()
        return response.text

    @abc.abstractmethod
    def _parse(
        self, ctx: ScraperContext, html: str
    ) -> tuple[Optional[float], Optional[str], dict]:
        ...

