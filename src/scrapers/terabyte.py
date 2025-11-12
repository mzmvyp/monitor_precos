from __future__ import annotations

import json
import random
import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from .selenium_base import SeleniumScraper, ScraperContext, LOGGER


def parse_brazilian_currency(value: str) -> float | None:
    """Parse preço brasileiro para float."""
    if not value:
        return None
    
    # Padrão: R$ 1.234,56 ou R$1234,56 ou R$ 1234,56 ou R$ 1234
    # Aceita com ou sem centavos
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


class TerabyteScraper(SeleniumScraper):
    store = "terabyte"
    
    def _get_html(self, ctx: ScraperContext) -> str:
        """Override para adicionar delay maior e verificação Cloudflare."""
        try:
            # Delay maior para evitar Cloudflare
            time.sleep(random.uniform(3.0, 5.0))
            
            self.driver.get(ctx.url)
            
            # Esperar mais tempo para Cloudflare processar
            time.sleep(random.uniform(5.0, 8.0))
            
            # 1. Aceitar cookies
            try:
                cookie_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUAR') or contains(text(), 'Continuar')]"))
                )
                cookie_button.click()
                LOGGER.info("Terabyte: Cookies aceitos")
                time.sleep(1)
            except TimeoutException:
                LOGGER.debug("Terabyte: Botão de cookies não encontrado")
            except Exception as e:
                LOGGER.debug(f"Terabyte: Erro ao aceitar cookies: {e}")
            
            # 2. Fechar popup Pushnews ("Fique de olho, consagrado!")
            try:
                pushnews_close = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Não quero') or contains(@class, 'pushnews')]"))
                )
                pushnews_close.click()
                LOGGER.info("Terabyte: Popup Pushnews fechado")
                time.sleep(1)
            except TimeoutException:
                LOGGER.debug("Terabyte: Popup Pushnews não encontrado")
            except Exception as e:
                LOGGER.debug(f"Terabyte: Erro ao fechar Pushnews: {e}")
            
            # 3. Fechar modal de ofertas (se existir)
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "modal"))
                )
                
                close_selectors = [
                    ".modal .close",
                    ".modal .btn-close",
                    ".modal [data-dismiss='modal']",
                    ".modal button[aria-label='Close']",
                    ".modal .fa-times",
                    ".modal .fa-close",
                    "button.close",
                    ".close-modal",
                ]
                
                for selector in close_selectors:
                    try:
                        close_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if close_button.is_displayed():
                            close_button.click()
                            LOGGER.info("Terabyte: Modal de ofertas fechado")
                            time.sleep(1)
                            break
                    except Exception:
                        continue
                        
            except TimeoutException:
                LOGGER.debug("Terabyte: Modal de ofertas não encontrado")
            except Exception as e:
                LOGGER.debug(f"Terabyte: Erro ao fechar modal: {e}")
            
            # Verificar se caiu no Cloudflare
            def _is_cloudflare(html: str) -> bool:
                return (
                    "Um momento" in html
                    or "cloudflare" in html.lower()
                    or "Please enable cookies" in html
                )

            page_source = self.driver.page_source
            if _is_cloudflare(page_source):
                LOGGER.warning("Terabyte: Detectado Cloudflare challenge, aguardando...")
                time.sleep(15)  # Aguardar Cloudflare resolver (aumentado para 15s)
                page_source = self.driver.page_source
                
                # Verificar novamente
                if _is_cloudflare(page_source):
                    LOGGER.error("Terabyte: Cloudflare ainda ativo após 15s, aguardando mais...")
                    time.sleep(10)  # Mais 10s
                    page_source = self.driver.page_source
            
            # Simular scroll mais lento
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(1.0, 2.0))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(random.uniform(1.0, 2.0))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 2.0))

            # Esperar preço carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#valVista")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".valVista")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".prod-new-price")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".prod-price")),
                    )
                )
            except TimeoutException:
                LOGGER.warning("Terabyte: Elemento de preço não apareceu após 10s")
            
            return self.driver.page_source
        except Exception as e:
            LOGGER.error(f"Erro ao coletar HTML Terabyte para {ctx.url}: {e}")
            raise

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")

        raw_price = ""
        
        # Primeiro: tentar pegar preço do container do produto principal
        product_container = soup.select_one(
            ".product-page, .prod-info, #infoBox, .productView, [class*='product-detail']"
        )
        if product_container:
            search_area = product_container
            LOGGER.debug("Terabyte: Usando container do produto")
        else:
            search_area = soup
            LOGGER.debug("Terabyte: Usando página inteira (fallback)")
        
        # Terabyte: buscar preço "por:" que é o preço com desconto
        page_text = search_area.get_text()
        
        # Procurar padrão "por: R$ X.XXX,XX" - mas filtrar preços muito baixos
        por_matches = re.findall(r'por:\s*R\$\s*([\d.,]+)', page_text, re.IGNORECASE)
        prices_collected: list[tuple[float, str]] = []
        for price_str in por_matches:
            price_val = parse_brazilian_currency(f"R$ {price_str}")
            if price_val and price_val > 200:  # ignorar banners baratos
                prices_collected.append((price_val, price_str))
        
        # Fallback 1: buscar elementos de preço bem conhecidos
        if not prices_collected:
            price_selectors = [
                "#valVista",
                ".valVista",
                ".preco-vista b",
                ".prod-new-price",
                ".prod-price",
                ".product__price",
                ".product-price",
                "[data-price]",
            ]
            for selector in price_selectors:
                elem = search_area.select_one(selector)
                if not elem:
                    continue
                text = elem.get_text(" ", strip=True)
                if not text and elem.has_attr("data-price"):
                    text = elem["data-price"]
                if not text:
                    continue
                match = re.search(r'R\$\s*[\d.,]+', text)
                if match:
                    price_val = parse_brazilian_currency(match.group())
                    if price_val and price_val > 200:
                        prices_collected.append((price_val, match.group().replace("R$", "").strip()))
                        LOGGER.debug("Terabyte: Preço encontrado via seletor %s: %s", selector, match.group())
                        break  # Priorizar o primeiro seletor válido
        
        if prices_collected:
            prices_collected.sort(reverse=True)
            raw_price = f"R$ {prices_collected[0][1]}"
            LOGGER.debug(
                "Terabyte: Preço final selecionado: %s (coletados %d candidatos)",
                raw_price,
                len(prices_collected),
            )
        # NÃO USAR FALLBACK GENÉRICO - Se não encontrou, retornar None
        
        # Fallback 2: buscar JSON-LD (structured data) - APENAS se for confiável
        if not raw_price:
            try:
                json_ld = soup.find("script", {"type": "application/ld+json"})
                if json_ld:
                    data = json.loads(json_ld.string)
                    # Pode ser um objeto ou lista de objetos
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    
                    # Procurar preço no JSON - APENAS se for offers válido
                    if "offers" in data and isinstance(data["offers"], dict):
                        price_val = data["offers"].get("price")
                        if price_val and float(price_val) > 200:  # Validar preço mínimo
                            raw_price = f"R$ {price_val}"
                            LOGGER.debug(f"Terabyte: Preço encontrado via JSON-LD: {raw_price}")
            except Exception as e:
                LOGGER.debug(f"Terabyte: Erro ao parsear JSON-LD: {e}")
        
        # NÃO USAR FALLBACK GENÉRICO - Se não encontrou, retornar None
        # Melhor retornar None do que pegar preço errado!

        price_value = parse_brazilian_currency(raw_price) if raw_price else None
        
        if not price_value:
            LOGGER.warning(f"Terabyte: Nenhum preço encontrado para {ctx.url}")
        else:
            LOGGER.info(f"Terabyte: Preço parseado: R$ {price_value}")

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
