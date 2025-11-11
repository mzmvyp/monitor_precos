from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import StoreScraper, ScraperContext, parse_brazilian_currency, LOGGER


class MercadoLivreScraper(StoreScraper):
    store = "mercadolivre"

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        raw_price = ""
        
        # Tentar extrair preço dos elementos andes-money-amount
        price_box = soup.select_one("span.andes-money-amount__fraction, .andes-money-amount__fraction")
        if price_box:
            raw_price = f"R$ {price_box.get_text(strip=True)}"
            cents = soup.select_one("span.andes-money-amount__cents, .andes-money-amount__cents")
            if cents:
                raw_price += f",{cents.get_text(strip=True)}"
            else:
                raw_price += ",00"  # Assumir centavos zero se não encontrado

        # Fallback: buscar por outros seletores
        if not raw_price:
            price_elem = soup.select_one(".ui-pdp-price__second-line, [class*='price-tag']")
            if price_elem:
                raw_price = price_elem.get_text(" ", strip=True)

        # Último fallback: buscar R$ no texto
        if not raw_price:
            for text in soup.stripped_strings:
                if "R$" in text and re.search(r'\d', text):
                    # Verificar se parece um preço válido
                    test_value = parse_brazilian_currency(text)
                    if test_value and test_value > 10:
                        raw_price = text
                        break

        price_value = parse_brazilian_currency(raw_price) if raw_price else None

        # Verificar disponibilidade
        availability = soup.select_one(".ui-pdp-stock-information__title, [class*='stock']")
        availability_text = ""
        if availability:
            availability_text = availability.get_text(" ", strip=True).lower()
        
        # Mercado Livre geralmente mostra "Estoque disponível" ou quantidade
        page_text = soup.get_text().lower()
        in_stock = (
            "estoque disponível" in page_text
            or "disponível" in availability_text
            or "em estoque" in page_text
            or bool(re.search(r'(\d+)\s*(unidade|disponível)', page_text))
        )
        
        # Se não encontrar indicação de falta de estoque, assumir disponível
        if not availability_text:
            in_stock = "esgotado" not in page_text and "indisponível" not in page_text

        return price_value, raw_price, {"in_stock": in_stock, "availability": availability_text}

