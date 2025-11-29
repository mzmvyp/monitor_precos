"""Módulo para buscar produtos no Google Shopping usando Selenium."""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

# Importar SeleniumScraper corretamente
try:
    from src.scrapers.selenium_base import SeleniumScraper
except ImportError:
    from scrapers.selenium_base import SeleniumScraper

LOGGER = logging.getLogger(__name__)


@dataclass
class ShoppingResult:
    """Resultado de busca no Google Shopping."""
    title: str
    price: float
    store: str
    url: str
    image_url: Optional[str] = None


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


class GoogleShoppingSearcher(SeleniumScraper):
    """Busca produtos no Google Shopping usando Selenium."""
    
    store = "googleshopping"
    
    def __init__(self):
        super().__init__()
    
    def _parse(self, ctx, html: str):
        """
        Método abstrato obrigatório - não usado para Google Shopping.
        Google Shopping usa _search() ao invés de _parse().
        """
        # Este método não é usado para Google Shopping
        # Retornar None pois não é um scraper de produto único
        return None, None, {"in_stock": None}
    
    def search_memory_ddr5_6000_cl30(self, capacity: str = "32GB") -> list[ShoppingResult]:
        """
        Busca memórias DDR5 6000MHz CL30 no Google Shopping.
        
        Args:
            capacity: Capacidade da memória (8GB, 16GB, 32GB)
        
        Returns:
            Lista de resultados ordenados por preço (menor primeiro)
        """
        # Query de busca otimizada
        query = f"memória RAM DDR5 {capacity} 6000MHz CL30"
        return self._search(query)
    
    def _search(self, query: str, max_results: int = 20) -> list[ShoppingResult]:
        """
        Busca produtos no Google Shopping usando Selenium.
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
        
        Returns:
            Lista de resultados ordenados por preço
        """
        # URL do Google Shopping
        search_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(query)}&hl=pt-BR&gl=BR"
        
        try:
            LOGGER.info(f"Buscando no Google Shopping: {query}")
            
            # Navegar para a página
            self.driver.get(search_url)
            time.sleep(3)  # Aguardar carregamento
            
            # Aguardar resultados aparecerem
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(5)  # Aguardar mais para carregar conteúdo dinâmico
            except Exception as e:
                LOGGER.warning(f"Timeout aguardando resultados do Google Shopping: {e}")
            
            # Obter HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            results = []
            
            # Google Shopping - seletores atualizados (estrutura pode variar)
            # Tentar múltiplos seletores possíveis
            product_containers = []
            
            # Estratégia 1: Buscar por data-docid (mais comum)
            containers = soup.select("div[data-docid]")
            if containers:
                product_containers = containers
                LOGGER.info(f"Encontrados {len(containers)} produtos via data-docid")
            else:
                # Estratégia 2: Buscar por classes conhecidas
                for selector in [
                    "div.sh-dgr__content",
                    "div.sh-dgr__grid-result", 
                    "div[data-cid]",
                    "div.sh-pr__product-results-grid > div",
                    "div[data-ved]",
                    "div.g"
                ]:
                    containers = soup.select(selector)
                    if containers and len(containers) > 2:  # Pelo menos 3 resultados
                        product_containers = containers
                        LOGGER.info(f"Encontrados {len(containers)} produtos via {selector}")
                        break
            
            if not product_containers:
                LOGGER.warning("Nenhum container de produto encontrado. Estrutura HTML pode ter mudado.")
                # Salvar HTML para debug
                with open("google_shopping_debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
                LOGGER.info("HTML salvo em google_shopping_debug.html para análise")
            
            for container in product_containers[:max_results * 2]:  # Pegar mais para filtrar
                try:
                    # Extrair título - múltiplos seletores
                    title_elem = (
                        container.select_one("h3") or
                        container.select_one("a h3") or
                        container.select_one(".sh-dgr__content h3") or
                        container.select_one("h4") or
                        container.select_one(".sh-pr__product-title")
                    )
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # Extrair preço - múltiplos seletores
                    price_elem = None
                    for selector in [
                        "span[aria-label*='R$']",
                        ".a8Pemb",
                        "span[data-dtype='d3ph']",
                        ".T14wmb",
                        ".sh-pr__product-price",
                        "span.sh-pr__product-price"
                    ]:
                        price_elem = container.select_one(selector)
                        if price_elem:
                            break
                    
                    if not price_elem:
                        # Tentar buscar no texto do container
                        container_text = container.get_text()
                        price_match = re.search(r'R\$\s*([\d\.\s]+(?:,\d{2})?)', container_text)
                        if not price_match:
                            continue
                        price_str = f"R$ {price_match.group(1)}"
                    else:
                        price_str = price_elem.get_text(strip=True)
                    
                    price_value = parse_brazilian_currency(price_str)
                    if not price_value or price_value < 100:  # Filtrar preços muito baixos
                        continue
                    
                    # Extrair loja
                    store_elem = None
                    for selector in [".aULzUe", ".E5ocAb", "span[data-dtype='d3sh']", ".sh-pr__seller-name"]:
                        store_elem = container.select_one(selector)
                        if store_elem:
                            break
                    store = store_elem.get_text(strip=True) if store_elem else "Loja não identificada"
                    
                    # Extrair URL
                    link_elem = container.select_one("a[href]")
                    if not link_elem:
                        continue
                    url = link_elem.get("href", "")
                    if url.startswith("/url?"):
                        # Extrair URL real do parâmetro
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                        if "q" in parsed:
                            url = parsed["q"][0]
                    elif not url.startswith("http"):
                        continue
                    
                    # Extrair imagem (opcional)
                    img_elem = container.select_one("img")
                    image_url = img_elem.get("src") if img_elem else None
                    
                    results.append(ShoppingResult(
                        title=title,
                        price=price_value,
                        store=store,
                        url=url,
                        image_url=image_url
                    ))
                    
                except Exception as e:
                    LOGGER.debug(f"Erro ao processar resultado: {e}")
                    continue
            
            # Ordenar por preço (menor primeiro)
            results.sort(key=lambda x: x.price)
            
            LOGGER.info(f"Encontrados {len(results)} resultados válidos no Google Shopping")
            return results[:max_results]
            
        except Exception as e:
            LOGGER.error(f"Erro ao buscar no Google Shopping: {e}")
            import traceback
            LOGGER.error(traceback.format_exc())
            return []
    
    def get_best_price(self, query: str) -> Optional[ShoppingResult]:
        """
        Retorna o menor preço encontrado para uma busca.
        
        Args:
            query: Termo de busca
        
        Returns:
            Resultado com menor preço ou None se não encontrar
        """
        results = self._search(query, max_results=10)
        if not results:
            return None
        return results[0]  # Já está ordenado por preço


def search_memory_ddr5_6000_cl30(capacity: str = "32GB") -> list[ShoppingResult]:
    """
    Função auxiliar para buscar memórias DDR5 6000MHz CL30.
    
    Args:
        capacity: Capacidade (8GB, 16GB, 32GB)
    
    Returns:
        Lista de resultados ordenados por preço
    """
    searcher = GoogleShoppingSearcher()
    return searcher.search_memory_ddr5_6000_cl30(capacity)

