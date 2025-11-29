from __future__ import annotations

import re

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


class MercadoLivreScraper(SeleniumScraper):
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
        
        # Verificar se está explicitamente indisponível
        if not in_stock:
            if any(word in page_text for word in ["esgotado", "indisponível", "sem estoque", "fora de estoque"]):
                in_stock = False
            elif not availability_text:
                # Se não há informação de disponibilidade, assumir disponível se tem preço
                in_stock = price_value is not None
        
        # Se não está disponível, não retornar preço
        if not in_stock:
            LOGGER.info(f"Mercado Livre: Produto sem estoque - {ctx.url}")
            return None, None, {"in_stock": False, "availability": availability_text}

        return price_value, raw_price, {"in_stock": True, "availability": availability_text}
