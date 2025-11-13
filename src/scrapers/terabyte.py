from __future__ import annotations

import json
import random
import re
import time
import os
import tempfile
import shutil
from pathlib import Path

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
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
    
    def _init_driver(self) -> None:
        """Override para Terabyte usando undetected-chromedriver (bypass Cloudflare)."""
        try:
            import undetected_chromedriver as uc
            from pathlib import Path
            
            LOGGER.info("Terabyte: Usando undetected-chromedriver para bypass Cloudflare")
            
            # Configurações do undetected-chromedriver
            options = uc.ChromeOptions()
            
            # TERABYTE: Usar headless por padrão (pode ser desabilitado via env se necessário)
            # Cloudflare pode detectar headless, mas com undetected-chromedriver funciona melhor
            use_headless = os.getenv("TERABYTE_HEADLESS", "true").lower() == "true"
            if use_headless:
                options.add_argument("--headless=new")
            else:
                # Modo visível apenas se explicitamente desabilitado (para debug)
                options.add_argument("--window-size=1366,768")
                options.add_argument("--start-maximized")
            
            # Configurações adicionais
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--lang=pt-BR")
            options.add_argument("--log-level=3")
            
            # Suprimir avisos de GPU/WebGL
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-webgl")
            options.add_argument("--disable-webgl2")
            options.add_argument("--disable-accelerated-2d-canvas")
            options.add_argument("--enable-unsafe-swiftshader")
            
            # Preferências
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            }
            options.add_experimental_option("prefs", prefs)
            
            # Verificar se há ChromeDriver manual instalado
            manual_chromedriver = Path.home() / ".chromedriver" / "chromedriver-win64" / "chromedriver.exe"
            env_chromedriver = os.getenv("CHROMEDRIVER_PATH")
            
            driver_executable_path = None
            if env_chromedriver and os.path.exists(env_chromedriver):
                # Fazer cópia temporária para evitar erro de permissão ao fazer patch
                temp_dir = Path(tempfile.gettempdir()) / "uc_chromedriver"
                temp_dir.mkdir(exist_ok=True)
                temp_driver = temp_dir / "chromedriver.exe"
                if not temp_driver.exists() or temp_driver.stat().st_mtime < Path(env_chromedriver).stat().st_mtime:
                    shutil.copy2(env_chromedriver, temp_driver)
                driver_executable_path = str(temp_driver)
            elif manual_chromedriver.exists():
                # Fazer cópia temporária para evitar erro de permissão ao fazer patch
                temp_dir = Path(tempfile.gettempdir()) / "uc_chromedriver"
                temp_dir.mkdir(exist_ok=True)
                temp_driver = temp_dir / "chromedriver.exe"
                if not temp_driver.exists() or temp_driver.stat().st_mtime < manual_chromedriver.stat().st_mtime:
                    shutil.copy2(manual_chromedriver, temp_driver)
                driver_executable_path = str(temp_driver)
            
            # Inicializar undetected-chromedriver
            # version_main: None = auto-detect, use_subprocess=True para melhor compatibilidade
            # Se não especificar driver_executable_path, o uc baixa e gerencia sua própria cópia
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=driver_executable_path,
                version_main=None,  # Auto-detect Chrome version
                use_subprocess=True,  # Melhor para bypass Cloudflare
            )
            
            self.driver.set_page_load_timeout(60)  # Timeout maior para Cloudflare
            self.driver.implicitly_wait(10)
            
            LOGGER.info("Terabyte: undetected-chromedriver inicializado com sucesso")
            
        except ImportError:
            LOGGER.warning("undetected-chromedriver não instalado. Instalando fallback para Selenium padrão...")
            LOGGER.warning("Execute: pip install undetected-chromedriver")
            
            # Fallback para Selenium padrão
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium import webdriver
            from pathlib import Path
            
            chrome_options = Options()
            
            use_headless = os.getenv("TERABYTE_HEADLESS", "true").lower() == "true"
            if use_headless:
                chrome_options.add_argument("--headless=new")
            else:
                chrome_options.add_argument("--window-size=1366,768")
                chrome_options.add_argument("--start-maximized")
            
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            )
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--lang=pt-BR")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-webgl2")
            chrome_options.add_argument("--disable-accelerated-2d-canvas")
            chrome_options.add_argument("--enable-unsafe-swiftshader")
            
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            manual_chromedriver = Path.home() / ".chromedriver" / "chromedriver-win64" / "chromedriver.exe"
            env_chromedriver = os.getenv("CHROMEDRIVER_PATH")
            
            driver_path = None
            if env_chromedriver and os.path.exists(env_chromedriver):
                driver_path = env_chromedriver
            elif manual_chromedriver.exists():
                driver_path = str(manual_chromedriver)
            else:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
            
            service = Service(driver_path, log_output=os.devnull)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['pt-BR', 'pt', 'en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: () => Promise.resolve({state: 'granted'})
                        })
                    });
                """
            })
            
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(10)
            
            LOGGER.warning("Terabyte: Usando Selenium padrão (fallback). Instale undetected-chromedriver para melhor bypass Cloudflare")
    
    def _is_driver_alive(self) -> bool:
        """Verifica se o driver ainda está válido."""
        if not self.driver:
            return False
        try:
            _ = self.driver.title
            return True
        except Exception:
            return False
    
    def _get_html(self, ctx: ScraperContext) -> str:
        """Navegação com comportamento humano para evitar Cloudflare."""
        try:
            # Verificar se driver ainda está válido
            if not self._is_driver_alive():
                LOGGER.warning("Terabyte: Driver inválido, reiniciando...")
                self._init_driver()
            
            # 1. Visitar home primeiro (como humano faria)
            LOGGER.info("Terabyte: Visitando home primeiro para parecer humano...")
            try:
                self.driver.get("https://www.terabyteshop.com.br/")
            except Exception as e:
                LOGGER.warning(f"Terabyte: Erro ao visitar home, reiniciando driver: {e}")
                self._init_driver()
                self.driver.get("https://www.terabyteshop.com.br/")
            time.sleep(random.uniform(3.0, 5.0))
            
            # 2. Aceitar cookies na home
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUAR') or contains(text(), 'Continuar')]"))
                )
                cookie_btn.click()
                LOGGER.info("Terabyte: Cookies aceitos na home")
                time.sleep(2)
            except TimeoutException:
                LOGGER.debug("Terabyte: Botão de cookies não encontrado na home")
            except Exception as e:
                LOGGER.debug(f"Terabyte: Erro ao aceitar cookies: {e}")
            
            # 3. Movimento de mouse aleatório (simular humano)
            try:
                actions = ActionChains(self.driver)
                for _ in range(2):
                    x = random.randint(100, 500)
                    y = random.randint(100, 400)
                    actions.move_by_offset(x, y).perform()
                    time.sleep(random.uniform(0.2, 0.5))
            except Exception:
                pass
            
            # 4. Agora sim, navegar para o produto
            LOGGER.info(f"Terabyte: Navegando para produto...")
            self.driver.get(ctx.url)
            
            # 5. Aguardar Cloudflare (se houver) - undetected-chromedriver geralmente resolve automaticamente
            time.sleep(random.uniform(5.0, 8.0))
            
            # 6. Verificar se passou do Cloudflare
            def _is_cloudflare(html: str) -> bool:
                return (
                    "Just a moment" in html
                    or "Checking your browser" in html
                    or "Um momento" in html
                    or "cloudflare" in html.lower()
                    or "Please enable cookies" in html
                    or "Ray ID" in html  # Cloudflare Ray ID
                )
            
            page_source = self.driver.page_source
            if _is_cloudflare(page_source):
                LOGGER.warning("Terabyte: Cloudflare detectado, aguardando resolução automática...")
                # undetected-chromedriver geralmente resolve sozinho, mas aguardar um pouco mais
                time.sleep(15)
                page_source = self.driver.page_source
                
                if _is_cloudflare(page_source):
                    LOGGER.warning("Terabyte: Cloudflare ainda ativo, aguardando mais...")
                    time.sleep(20)
                    page_source = self.driver.page_source
                    
                    if _is_cloudflare(page_source):
                        LOGGER.error("Terabyte: Cloudflare persistente após todas as tentativas")
            
            try:
                cookie_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUAR') or contains(text(), 'Continuar')]"))
                )
                cookie_button.click()
                LOGGER.info("Terabyte: Cookies aceitos na página do produto")
                time.sleep(1)
            except TimeoutException:
                LOGGER.debug("Terabyte: Botão de cookies não encontrado")
            except Exception as e:
                LOGGER.debug(f"Terabyte: Erro ao aceitar cookies: {e}")
            
            # 8. Fechar popup Pushnews ("Fique de olho, consagrado!")
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
            
            # 9. Fechar modal de ofertas (se existir)
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
            
            for i in range(3):
                scroll_height = random.randint(200, 400)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # 11. Aguardar preço carregar
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#valVista")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".valVista")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".prod-new-price")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".prod-price")),
                    )
                )
            except TimeoutException:
                LOGGER.warning("Terabyte: Elemento de preço não apareceu após 15s")
            
            # Verificar novamente se não está no Cloudflare
            final_html = self.driver.page_source
            if _is_cloudflare(final_html):
                LOGGER.error("Terabyte: Ainda bloqueado por Cloudflare após todas as tentativas")
                raise Exception("Bloqueado por Cloudflare - não foi possível acessar o produto")
            
            return final_html
        except Exception as e:
            LOGGER.error(f"Erro ao coletar HTML Terabyte para {ctx.url}: {e}")
            raise

    def _parse(self, ctx: ScraperContext, html: str):
        soup = BeautifulSoup(html, "html.parser")
        
        # Verificar se ainda está no Cloudflare
        if "Cloudflare" in html or "Just a moment" in html or "Checking your browser" in html:
            LOGGER.error("Terabyte: Ainda no Cloudflare após parse")
            return None, None, {"in_stock": None, "error": "Bloqueado por Cloudflare"}

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
            # CORREÇÃO: Ordenar do MENOR para o MAIOR preço (queremos o menor!)
            prices_collected.sort(reverse=False)
            raw_price = f"R$ {prices_collected[0][1]}"
            LOGGER.debug(
                "Terabyte: Preço final selecionado: %s (coletados %d candidatos, usando MENOR preço)",
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
