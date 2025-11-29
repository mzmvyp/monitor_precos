"""Scraper para Royal Caribbean."""
from __future__ import annotations

import json
import random
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from .selenium_base import SeleniumScraper, ScraperContext, LOGGER
from selenium.common.exceptions import WebDriverException


def parse_brl_price(value: str) -> float | None:
    """Parse preço em BRL para float."""
    if not value:
        return None
    
    # Extrair apenas números, pontos e vírgulas
    # Remove textos como "Total da cabine", "R$", etc.
    import re
    match = re.search(r'R?\$?\s*([\d.,]+)', value)
    if not match:
        LOGGER.debug(f"Nenhum número encontrado em: {value}")
        return None
    
    value = match.group(1).strip()
    
    # Se tem vírgula, é separador decimal brasileiro
    if "," in value:
        # Remove pontos (separador de milhar) e troca vírgula por ponto
        value = value.replace(".", "").replace(",", ".")
    
    try:
        return float(value)
    except ValueError:
        LOGGER.debug(f"Falha ao converter preço: {value}")
        return None


class RoyalCaribbeanScraper(SeleniumScraper):
    """Scraper para cruzeiros Royal Caribbean."""
    
    store = "royalcaribbean"
    currency = "BRL"
    
    def _get_html(self, ctx: ScraperContext) -> str:
        """Override para Royal Caribbean com delays adequados."""
        # Garantir que o driver existe (o base fecha após cada fetch)
        def ensure_driver():
            try:
                # _is_driver_alive é definido na base
                if not self._is_driver_alive():
                    LOGGER.warning("Royal Caribbean: Driver inexistente/inválido, reinicializando...")
                    self._init_driver()
            except Exception:
                self._init_driver()
        
        ensure_driver()
        
        try:
            # Delay inicial
            time.sleep(random.uniform(2.0, 4.0))
            
            self.driver.get(ctx.url)
            
            # Aguardar carregamento (página pesada)
            time.sleep(random.uniform(5.0, 8.0))
            
            # Verificar se precisa aceitar cookies
            page_source = self.driver.page_source
            if "cookie" in page_source.lower() or "aceitar" in page_source.lower():
                LOGGER.debug("Royal Caribbean: Possível banner de cookies detectado")
                time.sleep(2)
            
            # Scroll para carregar preços dinâmicos
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(random.uniform(1.0, 2.0))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(random.uniform(1.0, 2.0))
            
            return self.driver.page_source
        except WebDriverException as e:
            # Se o driver morreu entre o start e o get(), reiniciar uma vez e tentar novamente
            LOGGER.warning(f"Royal Caribbean: WebDriverException, tentando reiniciar driver... ({e})")
            self._init_driver()
            time.sleep(1.0)
            self.driver.get(ctx.url)
            time.sleep(random.uniform(5.0, 8.0))
            return self.driver.page_source
        except Exception as e:
            LOGGER.error(f"Erro ao coletar HTML Royal Caribbean para {ctx.url}: {e}")
            raise
    
    def _parse(self, ctx: ScraperContext, html: str) -> tuple[Optional[float], Optional[str], dict]:
        """Parse da página de checkout Royal Caribbean."""
        soup = BeautifulSoup(html, "html.parser")
        
        raw_price = ""
        price_value = None
        metadata = {}
        
        # Método 1: Buscar no JSON embutido (dados estruturados)
        try:
            # Royal Caribbean usa dados em scripts JSON
            scripts = soup.find_all("script", {"type": "application/json"})
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Procurar preço no JSON (estrutura pode variar)
                    if isinstance(data, dict):
                        # Buscar recursivamente por campos de preço
                        price_fields = ["price", "totalPrice", "total", "amount", "grandTotal"]
                        for field in price_fields:
                            if field in data:
                                raw_price = str(data[field])
                                LOGGER.debug(f"Royal Caribbean: Preço encontrado em JSON ({field}): {raw_price}")
                                break
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception as e:
            LOGGER.debug(f"Royal Caribbean: Erro ao buscar JSON: {e}")
        
        # Método 2: Buscar classes específicas de preço
        if not raw_price:
            price_selectors = [
                ".total-price",
                ".grand-total",
                "[class*='total']",
                "[class*='price']",
                "[data-price]",
                ".price-amount",
                ".cruise-price",
            ]
            
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(" ", strip=True)
                    # Verificar se tem R$ ou número
                    if "R$" in text or re.search(r'\d+[.,]\d+', text):
                        raw_price = text
                        LOGGER.debug(f"Royal Caribbean: Preço encontrado via {selector}: {raw_price}")
                        break
        
        # Método 3: Buscar no texto da página
        if not raw_price:
            page_text = soup.get_text()
            
            # Procurar padrões como "Total: R$ X.XXX,XX" ou "R$ X.XXX,XX"
            patterns = [
                r'Total[:\s]+R\$\s*([\d.,]+)',
                r'Grand Total[:\s]+R\$\s*([\d.,]+)',
                r'Valor Total[:\s]+R\$\s*([\d.,]+)',
                r'R\$\s*([\d.,]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    raw_price = f"R$ {match.group(1)}"
                    LOGGER.debug(f"Royal Caribbean: Preço encontrado via regex: {raw_price}")
                    break
        
        # Método 4: Buscar em atributos data-*
        if not raw_price:
            price_attrs = soup.find_all(attrs={"data-price": True})
            if price_attrs:
                raw_price = price_attrs[0].get("data-price", "")
                LOGGER.debug(f"Royal Caribbean: Preço encontrado em data-price: {raw_price}")
        
        # Converter preço
        if raw_price:
            price_value = parse_brl_price(raw_price)
        
        if not price_value:
            LOGGER.warning(f"Royal Caribbean: Nenhum preço encontrado para {ctx.url}")
        else:
            LOGGER.info(f"Royal Caribbean: Preço parseado: R$ {price_value}")
        
        # Extrair informações do cruzeiro da URL
        try:
            if "sailDate=" in ctx.url:
                sail_date = re.search(r'sailDate=([^&]+)', ctx.url)
                if sail_date:
                    metadata["sail_date"] = sail_date.group(1)
            
            if "shipCode=" in ctx.url:
                ship_code = re.search(r'shipCode=([^&]+)', ctx.url)
                if ship_code:
                    metadata["ship_code"] = ship_code.group(1)
            
            if "r0a=" in ctx.url:
                adults = re.search(r'r0a=(\d+)', ctx.url)
                if adults:
                    metadata["adults"] = int(adults.group(1))
        except Exception as e:
            LOGGER.debug(f"Royal Caribbean: Erro ao extrair metadata: {e}")
        
        # Disponibilidade (assumir disponível se encontrou preço)
        in_stock = price_value is not None
        
        # Se não está disponível, não retornar preço
        if not in_stock:
            LOGGER.info(f"Royal Caribbean: Produto sem estoque - {ctx.url}")
            metadata["in_stock"] = False
            return None, None, metadata
        
        metadata["in_stock"] = True
        return price_value, raw_price, metadata

