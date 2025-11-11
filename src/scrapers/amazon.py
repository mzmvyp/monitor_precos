from __future__ import annotations

import random
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from .base import StoreScraper, ScraperContext, parse_brazilian_currency, LOGGER


class AmazonScraper(StoreScraper):
    store = "amazon"

    def _get_html(self, ctx: ScraperContext) -> str:
        # Amazon costuma bloquear requisições repetidas; adicionamos pequenos delays randômicos.
        time.sleep(random.uniform(1.0, 2.0))
        return super()._get_html(ctx)

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        price = self._extract_price(soup)
        
        # Verificar disponibilidade
        availability = soup.select_one("#availability span, #availability")
        availability_text = ""
        if availability:
            availability_text = availability.get_text(" ", strip=True).lower()
        
        in_stock = (
            "disponível" in availability_text 
            or "em estoque" in availability_text
            or "in stock" in availability_text
        )

        raw_price = price["raw"] if price else None
        value = price["value"] if price else None

        return value, raw_price, {"in_stock": in_stock, "availability": availability_text}

    def _extract_price(self, soup: BeautifulSoup) -> Optional[dict]:
        # Seletores atualizados para Amazon Brasil
        price_selectors = [
            ".a-price .a-offscreen",  # Preço principal
            "#corePrice_feature_div .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            "span.a-price-whole",  # Parte inteira do preço
            "[data-a-color='price']",
        ]

        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                raw = element.get_text(" ", strip=True)
                # Filtrar apenas textos que contenham R$ e números
                if "R$" in raw or re.search(r'\d', raw):
                    value = parse_brazilian_currency(raw)
                    if value:
                        LOGGER.debug(f"Amazon preço encontrado com seletor {selector}: {raw}")
                        return {"raw": raw, "value": value}
        
        # Fallback: buscar no texto da página
        for text in soup.stripped_strings:
            if "R$" in text and re.search(r'\d{1,}[.,]\d{2}', text):
                value = parse_brazilian_currency(text)
                if value and value > 10:  # Filtrar valores muito baixos (provavelmente não são preços)
                    LOGGER.debug(f"Amazon preço encontrado no texto: {text}")
                    return {"raw": text, "value": value}
        
        return None

