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


class InpowerScraper(SeleniumScraper):
    store = "inpower"

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        # Tentar extrair do JSON embutido primeiro (mais confiável)
        script_tags = soup.find_all("script", type="application/ld+json")
        for script_tag in script_tags:
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict):
                    # Schema.org Product
                    if data.get("@type") == "Product":
                        offers = data.get("offers", {})
                        if isinstance(offers, dict):
                            price = offers.get("price")
                            if price:
                                try:
                                    price_value = float(price)
                                    raw_price = f"R$ {price_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                    return price_value, raw_price, {"in_stock": True}
                                except (ValueError, TypeError):
                                    pass
            except (json.JSONDecodeError, AttributeError):
                continue

        # Buscar preço no HTML - múltiplos seletores possíveis
        price_selectors = [
            ".price",
            ".preco",
            ".valor",
            ".product-price",
            ".price-current",
            ".preco-atual",
            "[data-price]",
            ".price-box .price",
            ".product-info .price",
            "span.price",
            "div.price",
            ".product-details .price",
            ".price-wrapper",
        ]

        price_value = None
        raw_price = None

        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                # Tentar obter de atributo data-price primeiro
                data_price = price_elem.get("data-price")
                if data_price:
                    try:
                        price_value = float(data_price)
                        raw_price = price_elem.get_text(strip=True)
                        break
                    except (ValueError, TypeError):
                        pass

                # Se não tem data-price, tentar parsear do texto
                price_text = price_elem.get_text(strip=True)
                if price_text:
                    parsed = parse_brazilian_currency(price_text)
                    if parsed:
                        price_value = parsed
                        raw_price = price_text
                        break

        # Fallback: buscar qualquer elemento com "R$" no texto
        if not price_value:
            price_pattern = re.compile(r'R\$\s*[\d\.\s]+(?:,\d{2})?', re.IGNORECASE)
            page_text = soup.get_text()
            matches = price_pattern.findall(page_text)
            
            # Filtrar valores muito altos ou muito baixos (provavelmente errados)
            # Para placas-mãe, SSDs, memórias, etc: mínimo R$ 100 (evita pegar preços de frete, parcelas, etc)
            # Máximo R$ 50.000 para produtos normais
            valid_prices = []
            for match in matches:
                parsed = parse_brazilian_currency(match)
                if parsed and 100 <= parsed <= 50000:  # Range mais restrito para evitar erros
                    valid_prices.append((parsed, match))
            
            # Se encontrou múltiplos preços, pegar o maior (geralmente é o preço do produto)
            # Preços muito baixos podem ser de frete, parcelas, etc
            if valid_prices:
                # Ordenar por valor e pegar o maior que seja razoável
                valid_prices.sort(key=lambda x: x[0], reverse=True)
                # Pegar o primeiro preço que seja >= 100 (já filtrado acima)
                price_value, raw_price = valid_prices[0]

        # Verificar disponibilidade
        page_text_lower = soup.get_text().lower()
        in_stock = (
            "indisponível" not in page_text_lower
            and "fora de estoque" not in page_text_lower
            and "esgotado" not in page_text_lower
            and "produto esgotado" not in page_text_lower
            and "sem estoque" not in page_text_lower
            and "avise-me" not in page_text_lower  # Botão "avise-me" geralmente indica sem estoque
        )

        # Se não está disponível, não retornar preço
        if not in_stock:
            LOGGER.info(f"Inpower: Produto sem estoque - {ctx.url}")
            return None, None, {"in_stock": False}

        if not price_value:
            LOGGER.warning(f"Inpower: Nenhum preço encontrado para {ctx.url}")
            return None, None, {"in_stock": True}

        LOGGER.info(f"Inpower: Preço parseado: R$ {price_value:.2f}")

        return price_value, raw_price or f"R$ {price_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), {"in_stock": True}

