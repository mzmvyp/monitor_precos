from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

from .selenium_base import SeleniumScraper, ScraperContext, LOGGER


def parse_brazilian_currency(value: str) -> float | None:
    """Parse preço brasileiro para float."""
    if not value:
        return None
    
    # Padrão: R$ 1.234,56 ou R$1234,56
    match = re.search(r'R\$\s*([0-9\.\s]+,[0-9]{2})', value)
    if not match:
        return None
    
    number = match.group(1)
    digits = number.replace(" ", "").replace(".", "").replace(",", ".")
    
    try:
        return float(digits)
    except ValueError:
        LOGGER.debug("Falha ao converter preço: %s", number)
        return None


class AmazonScraper(SeleniumScraper):
    store = "amazon"

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
                    if value and value > 50:  # Validar preço mínimo
                        LOGGER.debug(f"Amazon preço encontrado com seletor {selector}: {raw}")
                        return {"raw": raw, "value": value}
        
        # NÃO USAR FALLBACK GENÉRICO
        # Se não encontrou com seletores específicos, retornar None
        # Melhor retornar None do que pegar preço errado!
        LOGGER.warning("Amazon: Nenhum preço encontrado com seletores confiáveis")
        return None
