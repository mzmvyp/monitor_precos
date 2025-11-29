"""Base scraper usando Selenium para evitar bloqueios de bot."""
from __future__ import annotations

import abc
import logging
import os
import time
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import PriceSnapshot

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ScraperContext:
    store: str
    url: str


class SeleniumScraper(abc.ABC):
    """Base scraper usando Selenium com Chrome headless."""
    
    store: str
    currency: str = "BRL"
    
    def __init__(self) -> None:
        self.driver = None
        self._init_driver()
    
    def _init_driver(self) -> None:
        """Inicializa o Chrome driver com opções anti-detecção."""
        try:
            # Carregar .env se existir
            from pathlib import Path
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

            # Suprimir avisos do Selenium
            import warnings
            warnings.filterwarnings("ignore")

            # Suprimir logs do TensorFlow Lite e outros
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            os.environ['GRPC_VERBOSITY'] = 'ERROR'
            os.environ['GLOG_minloglevel'] = '3'
            
            chrome_options = Options()
            
            # Modo headless (sem interface gráfica)
            chrome_options.add_argument("--headless=new")
            
            # Opções anti-detecção
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # User agent realista
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Outras opções de performance e segurança
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--lang=pt-BR")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            
            # Silenciar TODOS os avisos e logs do Chrome
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-dev-tools")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Suprimir avisos específicos de GPU/WebGL e virtualização
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-webgl2")
            chrome_options.add_argument("--disable-accelerated-2d-canvas")
            chrome_options.add_argument("--disable-gpu-sandbox")
            chrome_options.add_argument("--use-gl=swiftshader")
            chrome_options.add_argument("--disable-features=UseChromeOSDirectVideoDecoder")
            
            # Suprimir erros de GPU/virtualização (redirecionar stderr)
            chrome_options.add_argument("--disable-gpu-process-crash-limit")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-gpu-logging'])
            
            # Desabilitar imagens para acelerar (opcional)
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Verificar SSL
            verify_ssl = os.getenv("SCRAPER_VERIFY_SSL", "true").lower()
            if verify_ssl in {"0", "false", "no"}:
                chrome_options.add_argument("--ignore-certificate-errors")
                chrome_options.add_argument("--allow-insecure-localhost")
            
            # Inicializar driver
            import sys
            from pathlib import Path

            # Verificar se há ChromeDriver manual instalado
            env_chromedriver = os.getenv("CHROMEDRIVER_PATH")

            # Procurar ChromeDriver em locais comuns
            exe_name = "chromedriver.exe" if os.name == "nt" else "chromedriver"
            manual_locations = [
                Path.home() / ".chromedriver" / exe_name,
                Path.home() / ".chromedriver" / "chromedriver-win64" / "chromedriver.exe",
                Path.home() / ".chromedriver" / "chromedriver-linux64" / "chromedriver",
                Path.home() / ".chromedriver" / "chromedriver-mac-x64" / "chromedriver",
            ]

            driver_path = None

            # Prioridade 1: Variável de ambiente
            if env_chromedriver and os.path.exists(env_chromedriver):
                driver_path = env_chromedriver
                LOGGER.info(f"Usando ChromeDriver de CHROMEDRIVER_PATH: {driver_path}")

            # Prioridade 2: Instalação manual
            if not driver_path:
                for location in manual_locations:
                    if location.exists():
                        driver_path = str(location)
                        LOGGER.info(f"Usando ChromeDriver manual: {driver_path}")
                        break

            # Prioridade 3: webdriver-manager (pode falhar com win32)
            if not driver_path:
                try:
                    LOGGER.info("Tentando usar webdriver-manager...")
                    driver_path = ChromeDriverManager().install()
                    
                    # Verificar se baixou win32 por engano
                    if 'win32' in driver_path.lower() and sys.maxsize > 2**32:
                        LOGGER.error("webdriver-manager baixou win32 em sistema 64 bits!")
                        raise RuntimeError(
                            "ChromeDriver incompatível (win32 vs win64).\n\n"
                            "SOLUÇÃO:\n"
                            "Execute: python instalar_chromedriver_manual.py\n"
                            "Isso vai baixar a versão correta (win64)."
                        )
                except Exception as e:
                    LOGGER.error(f"Erro com webdriver-manager: {e}")
                    raise RuntimeError(
                        "Falha ao instalar ChromeDriver automaticamente.\n\n"
                        "SOLUÇÃO:\n"
                        "Execute: python instalar_chromedriver_manual.py\n"
                        "Ou baixe manualmente: https://googlechromelabs.github.io/chrome-for-testing/"
                    )
            
            # Inicializar driver
            try:
                # Service com logs suprimidos
                service = Service(
                    driver_path,
                    log_output=os.devnull,  # Suprimir logs do ChromeDriver
                )
                
                # Suprimir stderr temporariamente
                import sys
                old_stderr = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Restaurar stderr
                sys.stderr.close()
                sys.stderr = old_stderr
                
                LOGGER.info(f"ChromeDriver inicializado com sucesso")
            except OSError as e:
                if "Win32" in str(e) or "193" in str(e):
                    raise RuntimeError(
                        f"ChromeDriver incompatível: {driver_path}\n\n"
                        "SOLUÇÃO:\n"
                        "1. Execute: python instalar_chromedriver_manual.py\n"
                        "2. Ou baixe manualmente de: https://googlechromelabs.github.io/chrome-for-testing/\n"
                        "   (Escolha win64, não win32)"
                    )
                else:
                    raise
            
            # Remover propriedade webdriver para evitar detecção
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                    """
                },
            )
            
            # Configurar timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            LOGGER.info(f"Selenium driver inicializado para {self.store}")
            
        except Exception as e:
            LOGGER.error(f"Erro ao inicializar Selenium driver: {e}")
            raise
    
    def __del__(self):
        """Fecha o driver ao destruir o objeto."""
        self.close()
    
    def close(self):
        """Fecha o driver do Selenium."""
        if self.driver:
            try:
                self.driver.quit()
                LOGGER.debug(f"Driver fechado para {self.store}")
            except Exception as e:
                LOGGER.debug(f"Erro ao fechar driver: {e}")
            finally:
                self.driver = None
    
    @retry(wait=wait_exponential(multiplier=2, min=2, max=30), stop=stop_after_attempt(3))
    def fetch(self, url: str) -> PriceSnapshot:
        """Coleta dados de um produto usando Selenium."""
        ctx = ScraperContext(store=self.store, url=url)
        
        try:
            html = self._get_html(ctx)
            price, raw_price, metadata = self._parse(ctx, html)
            
            return PriceSnapshot(
                product_id="",
                product_name="",
                category="",
                store=self.store,
                url=url,
                price=price,
                raw_price=raw_price,
                currency=self.currency,
                in_stock=metadata.get("in_stock"),
                fetched_at=datetime.now(timezone.utc),
                error=None,
                metadata=metadata,
            )
        except Exception as exc:
            LOGGER.exception("Erro ao coletar %s (%s)", url, self.store)
            return PriceSnapshot(
                product_id="",
                product_name="",
                category="",
                store=self.store,
                url=url,
                price=None,
                raw_price=None,
                currency=self.currency,
                in_stock=None,
                fetched_at=datetime.now(timezone.utc),
                error=str(exc),
                metadata={},
            )
        finally:
            # Evita deixar instâncias do Chrome/ChromeDriver abertas consumindo memória/CPU
            # Fecha sempre após cada fetch (mesmo em sucesso ou erro)
            try:
                self.close()
            except Exception:
                pass
    
    def _get_html(self, ctx: ScraperContext) -> str:
        """Navega até a URL e retorna o HTML."""
        try:
            # Validar se a URL corresponde à loja esperada
            url_lower = ctx.url.lower()
            store_domains = {
                "kabum": ["kabum.com.br"],
                "pichau": ["pichau.com.br"],
                "amazon": ["amazon.com.br", "amazon.com"],
                "terabyte": ["terabyteshop.com.br"],
                "mercadolivre": ["mercadolivre.com.br", "mercadolivre.com"],
                "inpower": ["inpower.com.br"],
            }
            
            expected_domains = store_domains.get(self.store, [])
            if expected_domains and not any(domain in url_lower for domain in expected_domains):
                LOGGER.warning(
                    f"⚠️ URL não corresponde à loja esperada: "
                    f"loja={self.store}, URL={ctx.url}. "
                    f"Verifique a configuração do produto."
                )
            
            # Inicializar driver se não existir ou não estiver válido
            if not self.driver or not self._is_driver_alive():
                if not self.driver:
                    LOGGER.debug(f"Inicializando driver para {self.store}")
                else:
                    LOGGER.warning("Driver inválido detectado, reiniciando...")
                self._init_driver()
            
            # Delay aleatório para simular comportamento humano
            time.sleep(random.uniform(1.0, 3.0))
            
            LOGGER.debug(f"Navegando para {ctx.url}")
            self.driver.get(ctx.url)
            
            # Aguardar página carregar
            time.sleep(random.uniform(2.0, 4.0))
            
            # Scroll para simular leitura
            self._simulate_human_behavior()
            
            # Obter HTML
            html = self.driver.page_source
            
            return html
            
        except TimeoutException:
            LOGGER.error(f"Timeout ao carregar {ctx.url}")
            raise
        except WebDriverException as e:
            LOGGER.error(f"Erro do WebDriver: {e}")
            raise
    
    def _is_driver_alive(self) -> bool:
        """Verifica se o driver ainda está válido."""
        if not self.driver:
            return False
        try:
            # Tentar obter o título da página atual
            _ = self.driver.title
            return True
        except Exception:
            return False
    
    def _simulate_human_behavior(self):
        """Simula comportamento humano com scroll e movimentos."""
        try:
            # Scroll suave para baixo
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            current_position = 0
            while current_position < total_height:
                # Scroll em incrementos aleatórios
                scroll_amount = random.randint(100, 300)
                current_position += scroll_amount
                
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.1, 0.3))
                
                # Parar no meio da página (simular leitura)
                if current_position > viewport_height and current_position < total_height / 2:
                    time.sleep(random.uniform(0.5, 1.0))
                    break
            
        except Exception as e:
            LOGGER.debug(f"Erro ao simular comportamento: {e}")
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Aguarda um elemento aparecer na página."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            LOGGER.warning(f"Elemento não encontrado: {by}={value}")
            return None
    
    @abc.abstractmethod
    def _parse(
        self, ctx: ScraperContext, html: str
    ) -> tuple[Optional[float], Optional[str], dict]:
        """Parse do HTML para extrair preço e metadados."""
        ...

