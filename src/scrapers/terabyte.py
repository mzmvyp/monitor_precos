from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import StoreScraper, ScraperContext, parse_brazilian_currency, LOGGER


class TerabyteScraper(StoreScraper):
    store = "terabyte"

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        raw_price = ""
        
        # Terabyte: buscar preço "por:" que é o preço com desconto
        page_text = soup.get_text()
        
        # Procurar padrão "por: R$ X.XXX,XX"
        por_match = re.search(r'por:\s*R\$\s*([\d.,]+)', page_text, re.IGNORECASE)
        if por_match:
            raw_price = f"R$ {por_match.group(1)}"
        else:
            # Fallback: buscar classe de preço
            price_elem = soup.select_one(".prod-new-price, .prod-price, [class*='price']")
            if price_elem:
                raw_price = price_elem.get_text(" ", strip=True)
                # Remover texto extra
                if "de:" in raw_price.lower():
                    # Se tem "De:" e "por:", pegar só o "por:"
                    if "por:" in raw_price.lower():
                        raw_price = raw_price.split("por:")[1].split("à vista")[0].strip()
                    else:
                        # Se só tem "De:", pegar o primeiro preço depois
                        parts = raw_price.split("de:", 1)
                        if len(parts) > 1:
                            match = re.search(r'R\$\s*[\d.,]+', parts[1])
                            if match:
                                raw_price = match.group()
                
                # Limpar texto extra
                if "à vista" in raw_price.lower():
                    raw_price = raw_price.split("à vista")[0].strip()
                if "12x" in raw_price.lower():
                    raw_price = raw_price.split("12x")[0].strip()

        price_value = parse_brazilian_currency(raw_price) if raw_price else None

        # Verificar disponibilidade
        page_text = soup.get_text().lower()
        in_stock = (
            "indisponível" not in page_text 
            and "fora de estoque" not in page_text
            and "esgotado" not in page_text
        )
        
        # Verificar botão de compra
        buy_button = soup.select_one("button[class*='buy'], button[class*='comprar'], .btn-comprar")
        if buy_button and "disabled" in buy_button.get("class", []):
            in_stock = False

        return price_value, raw_price, {"in_stock": in_stock}

