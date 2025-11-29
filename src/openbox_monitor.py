"""Monitor de Open Box da Kabum."""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup

from .alert_manager import AlertManager
from .scrapers.kabum import parse_brazilian_currency
from .scrapers.selenium_base import SeleniumScraper, ScraperContext

LOGGER = logging.getLogger(__name__)


@dataclass
class OpenBoxProduct:
    """Produto Open Box encontrado."""
    name: str
    price: float
    url: str
    category: str  # "memory", "psu", "cpu"
    found_at: datetime


class KabumOpenBoxScraper(SeleniumScraper):
    """Scraper para páginas de listagem Open Box da Kabum."""
    
    store = "kabum"
    
    def _parse(self, ctx: ScraperContext, html: str):
        """Parse de página de listagem Open Box."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Tentar extrair do JSON embutido (mais confiável)
        script_tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
        if script_tag:
            try:
                import json
                data = json.loads(script_tag.string)
                products_data = data.get("props", {}).get("pageProps", {}).get("products", [])
                
                if products_data:
                    # Converter para formato esperado
                    products_list = []
                    for prod in products_data:
                        try:
                            name = prod.get("name", "")
                            price = prod.get("price", 0) or prod.get("priceWithDiscount", 0)
                            url_prod = prod.get("url", "")
                            if url_prod and not url_prod.startswith("http"):
                                url_prod = f"https://www.kabum.com.br{url_prod}"
                            products_list.append({
                                "name": name,
                                "price": price,
                                "url": url_prod
                            })
                        except Exception:
                            continue
                    return products_list, None, {"source": "json"}
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                LOGGER.debug("Falha ao extrair JSON: %s", e)
        
        # Fallback: parse HTML
        products = []
        product_cards = soup.select(".productCard, .sc-fzqBZW, [class*='product-card']")
        
        for card in product_cards:
            try:
                # Nome do produto
                name_elem = card.select_one("h2, .productName, [class*='name']")
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)
                
                # URL
                link_elem = card.select_one("a[href]")
                if not link_elem:
                    continue
                url = link_elem.get("href", "")
                if url and not url.startswith("http"):
                    url = f"https://www.kabum.com.br{url}"
                
                # Preço
                price_elem = card.select_one(".priceCard, .finalPrice, [class*='price']")
                if not price_elem:
                    continue
                price_text = price_elem.get_text(strip=True)
                price = parse_brazilian_currency(price_text)
                
                if price:
                    products.append({
                        "name": name,
                        "price": price,
                        "url": url
                    })
            except Exception as e:
                LOGGER.debug(f"Erro ao parsear card: {e}")
                continue
        
        return products, None, {"source": "html"}
    
    def fetch_listing(self, url: str) -> list[dict]:
        """Busca produtos de uma página de listagem Open Box."""
        ctx = ScraperContext(store=self.store, url=url)
        
        try:
            html = self._get_html(ctx)
            products, _, _ = self._parse(ctx, html)
            
            # O _parse retorna lista de produtos
            if isinstance(products, list):
                return products
            
            return []
        except Exception as e:
            LOGGER.error(f"Erro ao buscar listagem Open Box: {e}")
            return []


class OpenBoxMonitor:
    """Monitor de produtos Open Box da Kabum."""
    
    def __init__(
        self,
        history_path: Path = Path("data/openbox_history.csv"),
        enable_alerts: bool = True,
    ):
        self.history_path = history_path
        self.alert_manager = AlertManager() if enable_alerts else None
        self.scraper = None
        self._ensure_history_file()
        
        # URLs de listagem Open Box
        self.urls = {
            "memory": "https://www.kabum.com.br/hardware/memoria-ram/ddr-5?page_number=1&page_size=20&facet_filters=eyJoYXNfb3Blbl9ib3giOlsidHJ1ZSJdfQ==&sort=most_searched",
            "psu": "https://www.kabum.com.br/hardware/fontes?page_number=1&page_size=20&facet_filters=eyJoYXNfb3Blbl9ib3giOlsidHJ1ZSJdfQ==&sort=most_searched",
            "cpu": "https://www.kabum.com.br/hardware/processadores/processador-amd?page_number=1&page_size=20&facet_filters=eyJoYXNfb3Blbl9ib3giOlsidHJ1ZSJdfQ==&sort=most_searched",
        }
    
    def _ensure_history_file(self) -> None:
        """Garante que o arquivo de histórico existe."""
        if not self.history_path.parent.exists():
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.history_path.exists():
            df = pd.DataFrame(columns=[
                "timestamp",
                "category",
                "name",
                "price",
                "url",
            ])
            df.to_csv(self.history_path, index=False, encoding="utf-8")
    
    def _init_scraper(self) -> None:
        """Inicializa o scraper se necessário."""
        if not self.scraper:
            self.scraper = KabumOpenBoxScraper()
    
    def _close_scraper(self) -> None:
        """Fecha o scraper."""
        if self.scraper:
            try:
                self.scraper.close()
            except Exception:
                pass
            self.scraper = None
    
    def _is_notebook_memory(self, name: str) -> bool:
        """Verifica se uma memória é para notebook (filtro robusto)."""
        name_upper = name.upper()
        
        # Palavras-chave que indicam notebook
        notebook_keywords = [
            "NOTEBOOK", "LAPTOP", "SO-DIMM", "SODIMM", 
            "DDR5 SODIMM", "DDR5 SO-DIMM",
            "PARA NOTEBOOK", "PARA LAPTOP", 
            "NOTEBOOK DDR5", "LAPTOP DDR5",
            "MOBILE", "PARA MOBILE", "MOBILE DDR5",
            "NOTEBOOK RAM", "LAPTOP RAM",
            "204 PIN", "204-PIN",  # SO-DIMM tem 204 pinos
            "260 PIN", "260-PIN",  # DDR5 SO-DIMM tem 260 pinos
        ]
        
        # Verificar palavras-chave
        if any(keyword in name_upper for keyword in notebook_keywords):
            return True
        
        # Verificar padrões específicos
        # SO-DIMM ou SODIMM sempre indica notebook
        if re.search(r'SO[-_]?DIMM', name_upper):
            return True
        
        # Verificar se menciona "notebook" ou "laptop" em qualquer parte
        if re.search(r'\b(NOTEBOOK|LAPTOP)\b', name_upper):
            return True
        
        return False
    
    def _filter_memory(self, products: list[dict]) -> list[OpenBoxProduct]:
        """Filtra memórias: 16GB ou 32GB+ e preço < R$ 1300, excluindo notebooks."""
        filtered = []
        
        for prod in products:
            name = prod.get("name", "")
            price = prod.get("price", 0)
            
            # Excluir memórias para notebook (verificação robusta)
            if self._is_notebook_memory(name):
                LOGGER.debug(f"Memória de notebook excluída: {name}")
                continue  # Pular memórias de notebook
            
            # Verificar se é 16GB ou 32GB+ (apenas desktop)
            name_upper = name.upper()
            has_32gb = "32GB" in name_upper or "32 GB" in name_upper
            has_64gb = "64GB" in name_upper or "64 GB" in name_upper
            has_128gb = "128GB" in name_upper or "128 GB" in name_upper
            has_16gb = "16GB" in name_upper or "16 GB" in name_upper
            
            # Aceitar 16GB ou 32GB+ (apenas desktop) e preço < R$ 1300
            if (has_16gb or has_32gb or has_64gb or has_128gb) and price < 1300:
                filtered.append(OpenBoxProduct(
                    name=name,
                    price=price,
                    url=prod.get("url", ""),
                    category="memory",
                    found_at=datetime.now(ZoneInfo("America/Sao_Paulo"))
                ))
        
        return filtered
    
    def _filter_psu(self, products: list[dict]) -> list[OpenBoxProduct]:
        """Filtra fontes: Gold e 750W+."""
        filtered = []
        
        for prod in products:
            name = prod.get("name", "").upper()
            price = prod.get("price", 0)
            
            # Verificar se é Gold
            is_gold = "GOLD" in name or "80 PLUS GOLD" in name
            
            # Verificar potência (750W ou mais)
            watt_match = re.search(r'(\d+)W', name)
            if watt_match:
                watts = int(watt_match.group(1))
                if is_gold and watts >= 750:
                    filtered.append(OpenBoxProduct(
                        name=prod.get("name", ""),
                        price=price,
                        url=prod.get("url", ""),
                        category="psu",
                        found_at=datetime.now(ZoneInfo("America/Sao_Paulo"))
                    ))
        
        return filtered
    
    def _filter_cpu(self, products: list[dict]) -> list[OpenBoxProduct]:
        """Filtra processadores: Ryzen 7xxx ou 9xxx."""
        filtered = []
        
        for prod in products:
            name = prod.get("name", "").upper()
            price = prod.get("price", 0)
            
            # Verificar se é Ryzen 7xxx ou 9xxx
            if "RYZEN" in name:
                # Padrões: 7xxx (ex: 7600X, 7700X, 7800X3D) ou 9xxx (ex: 9600X, 9700X)
                if re.search(r'7\d{3}', name) or re.search(r'9\d{3}', name):
                    filtered.append(OpenBoxProduct(
                        name=prod.get("name", ""),
                        price=price,
                        url=prod.get("url", ""),
                        category="cpu",
                        found_at=datetime.now(ZoneInfo("America/Sao_Paulo"))
                    ))
        
        return filtered
    
    def collect(self) -> list[OpenBoxProduct]:
        """Coleta produtos Open Box que atendem aos critérios."""
        self._init_scraper()
        
        all_products = []
        
        try:
            # Memórias
            LOGGER.info("Buscando memórias DDR5 Open Box...")
            memory_products = self.scraper.fetch_listing(self.urls["memory"])
            filtered_memory = self._filter_memory(memory_products)
            all_products.extend(filtered_memory)
            LOGGER.info(f"Encontradas {len(filtered_memory)} memórias Open Box que atendem critérios")
            
            time.sleep(5)  # Delay entre buscas
            
            # Fontes
            LOGGER.info("Buscando fontes Open Box...")
            psu_products = self.scraper.fetch_listing(self.urls["psu"])
            filtered_psu = self._filter_psu(psu_products)
            all_products.extend(filtered_psu)
            LOGGER.info(f"Encontradas {len(filtered_psu)} fontes Open Box que atendem critérios")
            
            time.sleep(5)
            
            # Processadores
            LOGGER.info("Buscando processadores AMD Ryzen Open Box...")
            cpu_products = self.scraper.fetch_listing(self.urls["cpu"])
            filtered_cpu = self._filter_cpu(cpu_products)
            all_products.extend(filtered_cpu)
            LOGGER.info(f"Encontrados {len(filtered_cpu)} processadores Open Box que atendem critérios")
            
        finally:
            self._close_scraper()
        
        # Verificar alertas ANTES de adicionar ao histórico (para detectar produtos novos)
        if self.alert_manager and all_products:
            self._check_alerts(all_products)
        
        # Fazer manutenção: remover produtos que não têm mais Open Box e limpar notebook
        self._maintain_history(all_products)
        
        # Salvar no histórico DEPOIS de verificar alertas e manutenção
        if all_products:
            self._append_history(all_products)
        
        return all_products
    
    def _maintain_history(self, current_products: list[OpenBoxProduct]) -> None:
        """
        Faz manutenção do histórico:
        1. Remove produtos que não têm mais Open Box disponível
        2. Remove memórias de notebook que possam estar no histórico
        """
        if not self.history_path.exists():
            return
        
        try:
            # Carregar histórico completo
            history = pd.read_csv(self.history_path, encoding="utf-8")
            if history.empty:
                return
            
            # Normalizar timestamps
            history["timestamp"] = pd.to_datetime(history["timestamp"], format="mixed", errors="coerce", utc=True)
            history = history[history["timestamp"].notna()]
            
            if history.empty:
                return
            
            # URLs dos produtos atuais (que ainda têm Open Box)
            current_urls = {prod.url for prod in current_products}
            
            # Filtrar histórico:
            # 1. Manter apenas produtos que ainda têm Open Box OU foram encontrados nas últimas 24h
            # 2. Remover memórias de notebook
            # 3. Remover produtos antigos sem Open Box (mais de 24h sem aparecer)
            
            now = datetime.now(timezone.utc)
            twenty_four_hours_ago = now - pd.Timedelta(hours=24)
            
            def should_keep(row):
                # Se é memória, verificar se é notebook
                if row["category"] == "memory":
                    name = str(row["name"])
                    if self._is_notebook_memory(name):
                        LOGGER.info(f"Removendo memória de notebook do histórico: {name}")
                        return False
                
                # Manter se ainda tem Open Box disponível
                if row["url"] in current_urls:
                    return True
                
                # Manter se foi encontrado nas últimas 24h
                row_timestamp = row["timestamp"]
                if pd.notna(row_timestamp):
                    if isinstance(row_timestamp, pd.Timestamp):
                        if row_timestamp.tz is None:
                            row_timestamp = row_timestamp.tz_localize(timezone.utc)
                        elif row_timestamp.tz != timezone.utc:
                            row_timestamp = row_timestamp.tz_convert(timezone.utc)
                        
                        if row_timestamp >= twenty_four_hours_ago:
                            return True
                
                # Remover produtos antigos sem Open Box
                LOGGER.debug(f"Removendo produto sem Open Box do histórico: {row['name']}")
                return False
            
            # Aplicar filtro
            history_filtered = history[history.apply(should_keep, axis=1)]
            
            # Salvar histórico limpo
            if len(history_filtered) < len(history):
                removed_count = len(history) - len(history_filtered)
                LOGGER.info(f"Manutenção: {removed_count} produtos removidos do histórico Open Box")
                history_filtered.to_csv(self.history_path, index=False, encoding="utf-8")
            else:
                LOGGER.debug("Nenhum produto removido na manutenção")
                
        except Exception as e:
            LOGGER.error(f"Erro ao fazer manutenção do histórico Open Box: {e}")
            # Não falhar completamente, apenas logar o erro
    
    def _append_history(self, products: list[OpenBoxProduct]) -> None:
        """Adiciona produtos ao histórico."""
        records = []
        for prod in products:
            records.append({
                "timestamp": prod.found_at.isoformat(),
                "category": prod.category,
                "name": prod.name,
                "price": prod.price,
                "url": prod.url,
            })
        
        df = pd.DataFrame(records)
        df.to_csv(
            self.history_path,
            mode="a",
            header=not self.history_path.exists(),
            index=False,
            encoding="utf-8"
        )
    
    def _check_alerts(self, products: list[OpenBoxProduct]) -> None:
        """Verifica e envia alertas para produtos Open Box."""
        if not self.alert_manager:
            return
        
        # Carregar histórico para verificar se produto é novo
        history = pd.DataFrame()
        if self.history_path.exists():
            history = pd.read_csv(self.history_path, encoding="utf-8")
            if not history.empty:
                # Corrigir parsing de data com timezone
                history["timestamp"] = pd.to_datetime(history["timestamp"], format="mixed", errors="coerce", utc=True)
                history = history[history["timestamp"].notna()]
        
        for prod in products:
            # Verificar se este produto JÁ EXISTE no histórico (produto antigo, não novo)
            is_new_product = True
            if not history.empty:
                # Verificar se URL já existe no histórico (produto já foi visto antes)
                existing = history[history["url"] == prod.url]
                if not existing.empty:
                    is_new_product = False
                    LOGGER.debug(f"Open Box já conhecido (não é novo): {prod.name}")
            
            # Só enviar email se for produto NOVO
            if not is_new_product:
                continue
            
            # Enviar email diretamente para Open Box (sempre que encontrar produto novo)
            product_id = f"openbox-{prod.category}-{hash(prod.url) % 100000}"
            product_name = prod.name
            
            # Preparar mensagem específica para Open Box
            category_name = {
                "memory": "💾 Memória DDR5",
                "psu": "⚡ Fonte de Alimentação",
                "cpu": "🔧 Processador AMD Ryzen"
            }.get(prod.category, "📦 Produto")
            
            subject = f"📦 OPEN BOX ENCONTRADO: {product_name}"
            
            brasilia_now = datetime.now(ZoneInfo("America/Sao_Paulo"))
            body = f"""🎯 PRODUTO OPEN BOX ENCONTRADO!

{category_name}

📦 Produto: {product_name}
💰 Preço: R$ {prod.price:.2f}
🏪 Loja: KABUM
🔗 Link: {prod.url}

ℹ️ Open Box = Produto com caixa aberta, devolução ou mostruário
   Funciona perfeitamente, mas pode ter sinais de uso

⏰ Alerta enviado em: {brasilia_now.strftime("%d/%m/%Y %H:%M:%S")}

---
Monitor de Preços Automático - Open Box
Aproveite essa oportunidade! 📦✨
"""
            
            # Enviar email diretamente
            alert_sent = self.alert_manager._send_email(subject, body)
            
            if alert_sent:
                LOGGER.info(f"📦 Email Open Box enviado: {prod.name} - R$ {prod.price:.2f}")
                
                # Registrar no histórico de alertas
                self.alert_manager._log_alert(
                    product_id=product_id,
                    product_name=f"[OPEN BOX] {product_name}",
                    store="kabum",
                    current_price=prod.price,
                    previous_price=0.0,
                    reduction_percent=0.0,
                    alert_sent=True,
                )
            else:
                LOGGER.warning(f"⚠️ Falha ao enviar email Open Box: {prod.name}")

