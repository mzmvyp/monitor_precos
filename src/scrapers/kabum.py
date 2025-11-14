from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from .selenium_base import SeleniumScraper, ScraperContext, LOGGER


def parse_brazilian_currency(value: str) -> float | None:
    """Parse preço brasileiro para float."""
    if not value:
        return None

    # Padrão: R$ 1.234,56 ou R$1234,56 ou R$ 1234 (aceita com ou sem centavos)
    match = re.search(r'R\$\s*([0-9\.\s]+(?:,[0-9]{1,2})?)', value)
    if not match:
        return None

    number = match.group(1)
    digits = number.replace(" ", "").replace(".", "")

    # Se tem vírgula, é separador decimal
    if "," in digits:
        digits = digits.replace(",", ".")
    # Se não tem vírgula, já é o valor inteiro

    try:
        return float(digits)
    except ValueError:
        LOGGER.debug("Falha ao converter preço: %s", number)
        return None


class KabumScraper(SeleniumScraper):
    store = "kabum"

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        # Detectar Open Box
        has_open_box = False
        open_box_price = None
        open_box_url = None

        # Buscar link ou badge de Open Box
        open_box_link = soup.find("a", href=re.compile(r"open-?box", re.I))
        if open_box_link:
            has_open_box = True
            open_box_url = open_box_link.get("href", "")
            if open_box_url and not open_box_url.startswith("http"):
                open_box_url = f"https://www.kabum.com.br{open_box_url}"

            # Tentar extrair preço do Open Box se estiver visível
            open_box_price_elem = open_box_link.find_next("span", class_=re.compile(r"price|valor", re.I))
            if open_box_price_elem:
                open_box_price_text = open_box_price_elem.get_text(strip=True)
                open_box_price = parse_brazilian_currency(open_box_price_text)

        # Alternativa: buscar texto "Open Box" ou "OpenBox"
        if not has_open_box:
            page_text = soup.get_text()
            if re.search(r"open\s*box", page_text, re.I):
                has_open_box = True

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
                    metadata = {
                        "in_stock": available,
                        "has_open_box": has_open_box,
                    }
                    if has_open_box:
                        metadata["open_box_url"] = open_box_url
                        if open_box_price:
                            metadata["open_box_price"] = open_box_price
                    return price_value, raw_price, metadata
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                LOGGER.debug("Falha ao extrair JSON do Kabum: %s", e)

        # Fallback: buscar no HTML - APENAS seletores confiáveis
        # Preço principal (com desconto)
        price_elem = soup.select_one("h4.text-4xl, h4.finalPrice, .finalPrice, .priceCard")
        raw_price = ""
        
        if price_elem:
            raw_price = price_elem.get_text(" ", strip=True)
            LOGGER.debug(f"Kabum: Preço encontrado no HTML: {raw_price}")
        
        # NÃO USAR FALLBACK GENÉRICO
        # Se não encontrou com seletores específicos, retornar None
        # Melhor retornar None do que pegar preço errado!

        price_value = parse_brazilian_currency(raw_price) if raw_price else None
        
        if not price_value:
            LOGGER.warning(f"Kabum: Nenhum preço encontrado para {ctx.url}")

        # Verificar disponibilidade
        available_text = soup.get_text().lower()
        in_stock = "indisponível" not in available_text and "fora de estoque" not in available_text

        metadata = {
            "in_stock": in_stock,
            "has_open_box": has_open_box,
        }
        if has_open_box:
            metadata["open_box_url"] = open_box_url
            if open_box_price:
                metadata["open_box_price"] = open_box_price

        return price_value, raw_price or None, metadata
