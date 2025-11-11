from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import StoreScraper, ScraperContext, parse_brazilian_currency, LOGGER


class PichauScraper(StoreScraper):
    store = "pichau"

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        raw_price = ""
        
        # Pichau: Buscar TODOS os elementos com price_vista e pegar o maior preço
        # Classe: mui-*-price_vista-*
        price_vista_elements = soup.select("[class*='price_vista']")
        max_price = 0
        for elem in price_vista_elements:
            text = elem.get_text(" ", strip=True)
            # Extrair valor: pode ter caracteres especiais como R$�1,809.99
            # O site pode usar PONTO como separador decimal (formato americano) ou vírgula (brasileiro)
            # Padrão: R$ seguido de dígitos com pontos/vírgulas
            # Aceita qualquer caractere não-dígito entre R$ e o número
            match = re.search(r'R\$\s*[^\d]*?([\d,.]+)', text)
            if match:
                price_str = match.group(1)
                try:
                    # Detectar formato baseado na posição dos separadores
                    if ',' in price_str and '.' in price_str:
                        # Verificar qual vem por último
                        last_comma = price_str.rfind(',')
                        last_dot = price_str.rfind('.')
                        
                        if last_dot > last_comma:
                            # Formato americano: 1,809.99 (vírgula para milhares, ponto para decimal)
                            value = float(price_str.replace(',', ''))
                        else:
                            # Formato brasileiro: 1.809,99 (ponto para milhares, vírgula para decimal)
                            value = float(price_str.replace('.', '').replace(',', '.'))
                    elif ',' in price_str:
                        # Formato brasileiro sem milhares: 234,56
                        value = float(price_str.replace(',', '.'))
                    else:
                        # Formato americano: 1234.56
                        value = float(price_str)
                    
                    if value > max_price and value > 100:
                        max_price = value
                        # Normalizar para formato brasileiro
                        raw_price = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                except:
                    continue
        
        # Fallback: buscar "por:" seguido de preço
        if not raw_price:
            page_text = soup.get_text()
            por_match = re.search(r'por:\s*R\$?\s*[^\d]*([\d.]+,\d{2})', page_text, re.IGNORECASE)
            if por_match:
                raw_price = f"R$ {por_match.group(1)}"
        
        # Último fallback: buscar qualquer preço > R$ 100
        if not raw_price:
            page_text = soup.get_text()
            all_prices = re.findall(r'R\$?\s*[^\d]*([\d.]+,\d{2})', page_text)
            for price_str in all_prices:
                try:
                    value = float(price_str.replace('.', '').replace(',', '.'))
                    if value > 100:  # Preço mínimo razoável
                        raw_price = f"R$ {price_str}"
                        break
                except:
                    continue

        price_value = parse_brazilian_currency(raw_price) if raw_price else None

        # Verificar disponibilidade
        page_text = soup.get_text().lower()
        in_stock = (
            "indisponível" not in page_text 
            and "fora de estoque" not in page_text
            and "esgotado" not in page_text
            and "produto indisponível" not in page_text
        )
        
        # Verificar botão de compra
        buy_button = soup.select_one("button[class*='add'], button[class*='comprar']")
        if buy_button:
            button_text = buy_button.get_text().lower()
            if "indisponível" in button_text or "esgotado" in button_text:
                in_stock = False

        return price_value, raw_price, {"in_stock": in_stock}

