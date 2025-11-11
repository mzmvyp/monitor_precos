from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from .base import StoreScraper, ScraperContext, parse_brazilian_currency, LOGGER


class KabumScraper(StoreScraper):
    store = "kabum"

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        # Tentar extrair do JSON embutido (mais confiável)
        script_tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
        if script_tag:
            try:
                data = json.loads(script_tag.string)
                product_data = data.get("props", {}).get("pageProps", {}).get("product", {})
                
                # Preço com desconto PIX ou preço promocional
                price_value = product_data.get("prices", {}).get("priceWithDiscount")
                if not price_value:
                    price_value = product_data.get("price")
                
                available = product_data.get("available", False)
                
                if price_value:
                    raw_price = f"R$ {price_value:.2f}".replace(".", ",")
                    return price_value, raw_price, {"in_stock": available}
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                LOGGER.debug("Falha ao extrair JSON do Kabum: %s", e)

        # Fallback: buscar no HTML
        # Preço principal (com desconto)
        price_elem = soup.select_one("h4.text-4xl, h4.finalPrice, .finalPrice")
        raw_price = ""
        
        if price_elem:
            raw_price = price_elem.get_text(" ", strip=True)
        
        if not raw_price:
            # Buscar qualquer texto com R$
            for text in soup.stripped_strings:
                if "R$" in text and re.search(r'\d', text):
                    raw_price = text
                    break

        price_value = parse_brazilian_currency(raw_price) if raw_price else None

        # Verificar disponibilidade
        available_text = soup.get_text().lower()
        in_stock = "indisponível" not in available_text and "fora de estoque" not in available_text

        return price_value, raw_price or None, {"in_stock": in_stock}

