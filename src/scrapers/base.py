from __future__ import annotations

import abc
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

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
        
        # Inicializar cookies visitando a página inicial
        self._initialize_session()

    @staticmethod
    def _create_session():
        import requests

        session = requests.Session()
        session.headers.update(
            {
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "cache-control": "max-age=0",
                "dnt": "1",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "connection": "keep-alive",
            }
        )
        return session
    
    def _initialize_session(self) -> None:
        """Visita a página inicial do site para obter cookies de sessão."""
        import time
        import random
        
        # Mapear domínios base por loja
        base_urls = {
            "pichau": "https://www.pichau.com.br/",
            "terabyte": "https://www.terabyteshop.com.br/",
            "kabum": "https://www.kabum.com.br/",
            "amazon": "https://www.amazon.com.br/",
            "mercadolivre": "https://www.mercadolivre.com.br/",
        }
        
        base_url = base_urls.get(self.store)
        if not base_url:
            return
        
        try:
            # Pequeno delay inicial
            time.sleep(random.uniform(0.5, 1.5))
            
            # Visitar página inicial para obter cookies
            response = self.session.get(
                base_url,
                timeout=10,
                allow_redirects=True,
            )
            
            # Se obteve resposta, aguardar um pouco antes de fazer scraping
            if response.status_code == 200:
                time.sleep(random.uniform(1.0, 2.0))
                LOGGER.debug(f"Sessão inicializada para {self.store}")
        except Exception as e:  # noqa: BLE001
            LOGGER.debug(f"Erro ao inicializar sessão para {self.store}: {e}")

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

    @retry(wait=wait_exponential(multiplier=2, min=2, max=30), stop=stop_after_attempt(5))
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
        import time
        import random
        
        # Delay menor já que temos delay na inicialização
        time.sleep(random.uniform(0.5, 1.5))
        
        response = self.session.get(
            ctx.url,
            timeout=20,
            headers=self._build_request_headers(ctx),
            allow_redirects=True,
        )
        
        # Se receber 403, tentar uma vez com delay maior
        if response.status_code == 403:
            LOGGER.warning(f"Recebido 403 para {ctx.url}, tentando novamente após delay...")
            time.sleep(random.uniform(3.0, 5.0))
            
            # Tentar novamente com headers ligeiramente diferentes
            response = self.session.get(
                ctx.url,
                timeout=20,
                headers=self._build_request_headers(ctx),
                allow_redirects=True,
            )
        
        response.raise_for_status()
        return response.text

    def _build_request_headers(self, ctx: ScraperContext) -> dict[str, str]:
        parsed = urlparse(ctx.url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"
        return {
            "accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "referer": referer,
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }

    @abc.abstractmethod
    def _parse(
        self, ctx: ScraperContext, html: str
    ) -> tuple[Optional[float], Optional[str], dict]:
        ...

