"""State Management para Monitor de Preços - Reflex."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import reflex as rx
import yaml

from src.flight_monitor import FlightMonitor
from src.price_monitor import PriceMonitor

# Caminhos dos arquivos
CONFIG_PATH = Path("config/products.yaml")
HISTORY_PATH = Path("data/price_history.csv")
FLIGHT_CONFIG_PATH = Path("config/flights.yaml")
FLIGHT_HISTORY_PATH = Path("data/flight_history.csv")


class PriceMonitorState(rx.State):
    """Estado principal da aplicação."""

    # ============================================================
    # ESTADO DE DADOS
    # ============================================================

    # Produtos e histórico
    products: dict[str, Any] = {}
    history_df: pd.DataFrame = pd.DataFrame()
    latest_prices_df: pd.DataFrame = pd.DataFrame()
    config_data: dict[str, Any] = {}

    # Voos
    flights_df: pd.DataFrame = pd.DataFrame()

    # ============================================================
    # ESTADO DA UI - FILTROS
    # ============================================================

    # Filtros do Dashboard
    selected_category: str = "Todas"
    selected_stores: list[str] = ["Todas"]
    price_filter_enabled: bool = False
    price_min: float = 0
    price_max: float = 5000
    search_term: str = ""
    sort_by: str = "Menor preço"
    view_mode: str = "Compacta"

    # Filtros do Gerenciamento
    manage_search: str = ""
    manage_category: str = "Todas"
    manage_status: str = "Todos"

    # ============================================================
    # ESTADO DA UI - NAVEGAÇÃO
    # ============================================================

    current_tab: str = "dashboard"  # dashboard, manage, stats, flights, about
    current_dashboard_view: str = "highlights"  # highlights, catalog

    # ============================================================
    # ESTADO DA UI - FORMULÁRIOS
    # ============================================================

    # Form: Adicionar Produto
    form_name: str = ""
    form_id: str = ""
    form_category: str = "cpu"
    form_desired_price: float = 1000.0
    form_enabled: bool = True
    form_urls: list[dict[str, str]] = []

    # Form: Editar Produto
    edit_product_id: str = ""
    edit_name: str = ""
    edit_category: str = "cpu"
    edit_desired_price: float = 1000.0
    edit_enabled: bool = True

    # ============================================================
    # ESTADO DA UI - LOADING & ERRORS
    # ============================================================

    is_loading: bool = False
    is_collecting: bool = False
    error_message: str = ""
    success_message: str = ""
    collection_progress: str = ""

    # ============================================================
    # ESTATÍSTICAS
    # ============================================================

    total_products: int = 0
    active_products: int = 0
    total_urls: int = 0
    total_savings: float = 0.0
    products_below_target: int = 0
    total_checks: int = 0

    # ============================================================
    # MÉTODO DE INICIALIZAÇÃO
    # ============================================================

    def on_load(self):
        """Carrega dados iniciais quando a página é carregada."""
        self.load_all_data()

    # ============================================================
    # CARREGAMENTO DE DADOS
    # ============================================================

    def load_all_data(self):
        """Carrega todos os dados necessários."""
        self.load_config()
        self.load_products()
        self.load_history()
        self.calculate_statistics()

    def load_config(self):
        """Carrega configuração do YAML."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f)
        except Exception as e:
            self.error_message = f"Erro ao carregar configuração: {e}"
            self.config_data = {"items": []}

    def save_config(self):
        """Salva configuração no YAML."""
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.config_data,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
            self.success_message = "Configuração salva com sucesso!"
        except Exception as e:
            self.error_message = f"Erro ao salvar configuração: {e}"

    def load_products(self):
        """Carrega produtos do PriceMonitor."""
        try:
            monitor = PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)
            self.products = {prod_id: prod for prod_id, prod in monitor.products.items()}
        except Exception as e:
            self.error_message = f"Erro ao carregar produtos: {e}"
            self.products = {}

    def load_history(self):
        """Carrega histórico de preços."""
        try:
            monitor = PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)
            self.history_df = monitor.load_history()

            if not self.history_df.empty:
                self.history_df["timestamp"] = pd.to_datetime(
                    self.history_df["timestamp"], utc=True
                )

                # Calcular latest prices
                self.latest_prices_df = (
                    self.history_df.sort_values("timestamp")
                    .groupby(["product_id", "store"])
                    .tail(1)
                    .reset_index(drop=True)
                )
        except Exception as e:
            self.error_message = f"Erro ao carregar histórico: {e}"
            self.history_df = pd.DataFrame()
            self.latest_prices_df = pd.DataFrame()

    def calculate_statistics(self):
        """Calcula estatísticas gerais."""
        try:
            # Produtos
            self.total_products = len(self.config_data.get("items", []))
            self.active_products = sum(
                1 for item in self.config_data.get("items", []) if item.get("enabled", True)
            )
            self.total_urls = sum(
                len(item.get("urls", []))
                for item in self.config_data.get("items", [])
            )

            # Verificações
            self.total_checks = len(self.history_df) if not self.history_df.empty else 0

            # Economia
            self.total_savings = 0.0
            self.products_below_target = 0

            if not self.latest_prices_df.empty:
                for _, row in self.latest_prices_df.iterrows():
                    product = self.products.get(row["product_id"])
                    if (
                        product
                        and pd.notna(row["price"])
                        and pd.notna(product.desired_price)
                        and row["price"] <= product.desired_price
                    ):
                        savings = product.desired_price - row["price"]
                        self.total_savings += savings
                        self.products_below_target += 1

        except Exception as e:
            self.error_message = f"Erro ao calcular estatísticas: {e}"

    # ============================================================
    # AÇÕES - COLETA DE PREÇOS
    # ============================================================

    async def collect_prices(self, product_ids: list[str] | None = None):
        """Coleta preços dos produtos."""
        self.is_collecting = True
        self.collection_progress = "Iniciando coleta..."
        self.error_message = ""

        try:
            monitor = PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)

            self.collection_progress = "Coletando preços... Isso pode demorar alguns minutos."

            snapshots = monitor.collect(product_ids=product_ids)

            if snapshots:
                self.success_message = f"✅ Coleta finalizada: {len(snapshots)} registros coletados!"
                # Recarregar dados
                self.load_all_data()
            else:
                self.error_message = "⚠️ Nenhum preço foi coletado."

        except RuntimeError as e:
            error_msg = str(e)
            if "ChromeDriver" in error_msg or "Chrome binary" in error_msg:
                self.error_message = "❌ Erro: ChromeDriver não instalado! Execute: python instalar_chromedriver_manual.py"
            else:
                self.error_message = f"❌ Erro ao coletar preços: {error_msg}"
        except Exception as e:
            self.error_message = f"❌ Erro inesperado: {str(e)}"
        finally:
            self.is_collecting = False
            self.collection_progress = ""

    # ============================================================
    # AÇÕES - GERENCIAMENTO DE PRODUTOS
    # ============================================================

    def add_product(
        self,
        product_id: str,
        name: str,
        category: str,
        desired_price: float,
        enabled: bool,
        urls: list[dict[str, str]],
    ):
        """Adiciona novo produto."""
        # Validações
        if not product_id or not name:
            self.error_message = "❌ Nome e ID são obrigatórios!"
            return

        if any(item["id"] == product_id for item in self.config_data.get("items", [])):
            self.error_message = f"❌ Já existe um produto com o ID '{product_id}'!"
            return

        if not urls:
            self.error_message = "❌ Adicione pelo menos uma URL!"
            return

        # Adicionar produto
        new_product = {
            "id": product_id,
            "name": name,
            "category": category,
            "desired_price": desired_price,
            "enabled": enabled,
            "urls": urls,
        }

        if "items" not in self.config_data:
            self.config_data["items"] = []

        self.config_data["items"].append(new_product)
        self.save_config()
        self.load_all_data()

        self.success_message = f"✅ Produto '{name}' adicionado com sucesso!"

        # Limpar formulário
        self.form_name = ""
        self.form_id = ""
        self.form_desired_price = 1000.0

    def update_product(self, product_id: str, updates: dict[str, Any]):
        """Atualiza produto existente."""
        for item in self.config_data.get("items", []):
            if item["id"] == product_id:
                item.update(updates)
                break

        self.save_config()
        self.load_all_data()
        self.success_message = "✅ Produto atualizado!"

    def delete_product(self, product_id: str):
        """Remove produto."""
        if "items" in self.config_data:
            self.config_data["items"] = [
                item for item in self.config_data["items"] if item["id"] != product_id
            ]

        self.save_config()
        self.load_all_data()
        self.success_message = "✅ Produto removido!"

    def toggle_product(self, product_id: str, enabled: bool):
        """Ativa/desativa produto."""
        for item in self.config_data.get("items", []):
            if item["id"] == product_id:
                item["enabled"] = enabled
                break

        self.save_config()
        self.load_all_data()

    def duplicate_product(self, product_id: str):
        """Duplica produto."""
        for item in self.config_data.get("items", []):
            if item["id"] == product_id:
                new_item = item.copy()
                new_item["id"] = f"{product_id}-copy-{len(self.config_data['items'])}"
                new_item["name"] = f"{item['name']} (Cópia)"
                new_item["enabled"] = False
                self.config_data["items"].append(new_item)
                break

        self.save_config()
        self.load_all_data()
        self.success_message = "✅ Produto duplicado!"

    # ============================================================
    # AÇÕES - IMPORT/EXPORT
    # ============================================================

    def export_csv(self) -> str:
        """Exporta produtos para CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["id", "name", "category", "desired_price", "enabled", "store", "url"])

        for item in self.config_data.get("items", []):
            for url_data in item.get("urls", []):
                writer.writerow(
                    [
                        item["id"],
                        item["name"],
                        item["category"],
                        item.get("desired_price", 0),
                        item.get("enabled", True),
                        url_data["store"],
                        url_data["url"],
                    ]
                )

        return output.getvalue()

    def export_json(self) -> str:
        """Exporta produtos para JSON."""
        return json.dumps(self.config_data, ensure_ascii=False, indent=2)

    def import_csv(self, content: str):
        """Importa produtos de CSV."""
        try:
            reader = csv.DictReader(io.StringIO(content))

            products = {}
            for row in reader:
                product_id = row["id"]
                if product_id not in products:
                    products[product_id] = {
                        "id": product_id,
                        "name": row["name"],
                        "category": row["category"],
                        "desired_price": float(row["desired_price"]),
                        "enabled": row["enabled"].lower() == "true",
                        "urls": [],
                    }

                products[product_id]["urls"].append(
                    {"store": row["store"], "url": row["url"]}
                )

            self.config_data = {"items": list(products.values())}
            self.save_config()
            self.load_all_data()
            self.success_message = f"✅ {len(products)} produtos importados!"

        except Exception as e:
            self.error_message = f"❌ Erro ao importar: {e}"

    def import_json(self, content: str):
        """Importa produtos de JSON."""
        try:
            self.config_data = json.loads(content)
            self.save_config()
            self.load_all_data()
            self.success_message = "✅ Produtos importados com sucesso!"
        except Exception as e:
            self.error_message = f"❌ Erro ao importar: {e}"

    # ============================================================
    # AÇÕES - VOOS
    # ============================================================

    async def collect_flights(self):
        """Busca voos."""
        self.is_loading = True
        self.error_message = ""

        try:
            flight_monitor = FlightMonitor(
                config_path=FLIGHT_CONFIG_PATH, history_path=FLIGHT_HISTORY_PATH
            )
            flights = flight_monitor.collect()
            flight_monitor.close()

            if flights:
                self.success_message = f"✅ {len(flights)} voos encontrados!"
                self.load_flights()
            else:
                self.error_message = "📭 Nenhum voo encontrado"

        except Exception as e:
            self.error_message = f"❌ Erro: {e}"
        finally:
            self.is_loading = False

    def load_flights(self):
        """Carrega histórico de voos."""
        try:
            if FLIGHT_HISTORY_PATH.exists():
                flight_monitor = FlightMonitor(
                    config_path=FLIGHT_CONFIG_PATH, history_path=FLIGHT_HISTORY_PATH
                )
                self.flights_df = flight_monitor.get_latest_flights()
        except Exception as e:
            self.error_message = f"❌ Erro ao carregar voos: {e}"
            self.flights_df = pd.DataFrame()

    # ============================================================
    # HELPERS - FILTROS
    # ============================================================

    def get_filtered_products(self) -> pd.DataFrame:
        """Retorna produtos filtrados baseado nos filtros ativos."""
        if self.latest_prices_df.empty:
            return pd.DataFrame()

        df = self.latest_prices_df.copy()

        # Filtrar categoria
        if self.selected_category != "Todas":
            df = df[df["category"] == self.selected_category]

        # Filtrar lojas
        if "Todas" not in self.selected_stores:
            df = df[df["store"].isin(self.selected_stores)]

        # Filtrar produtos ativos
        active_ids = {
            item["id"]
            for item in self.config_data.get("items", [])
            if item.get("enabled", True)
        }
        df = df[df["product_id"].isin(active_ids)]

        # Filtrar por preço
        if self.price_filter_enabled:
            df = df[
                (df["price"] >= self.price_min) & (df["price"] <= self.price_max)
            ]

        # Busca por texto
        if self.search_term:
            df = df[
                df["product_name"].str.contains(
                    self.search_term, case=False, na=False
                )
            ]

        # Ordenação
        if self.sort_by == "Menor preço":
            df = df.sort_values("price", ascending=True)
        elif self.sort_by == "Maior preço":
            df = df.sort_values("price", ascending=False)
        elif self.sort_by == "Nome (A-Z)":
            df = df.sort_values("product_name")
        elif self.sort_by == "Loja":
            df = df.sort_values("store")

        return df

    def get_category_color(self, category: str) -> str:
        """Retorna cor da categoria."""
        colors = {
            "cpu": "#FF6B6B",
            "motherboard": "#4ECDC4",
            "memory": "#45B7D1",
            "storage": "#96CEB4",
            "gpu": "#DDA15E",
            "psu": "#BC6C25",
            "cooler": "#588157",
            "case": "#6C757D",
            "cruise": "#E63946",
            "other": "#495057",
        }
        return colors.get(category, "#6C757D")

    # ============================================================
    # HELPERS - DATA STALENESS
    # ============================================================

    def get_last_update_info(self) -> dict[str, Any]:
        """Retorna informações sobre a última atualização."""
        if self.history_df.empty:
            return {
                "has_data": False,
                "message": "Nenhum dado coletado ainda",
                "type": "info",
            }

        last_update = self.history_df["timestamp"].max()
        time_since_update = datetime.now(timezone.utc) - last_update
        hours_since = time_since_update.total_seconds() / 3600

        brasilia_tz = ZoneInfo("America/Sao_Paulo")
        last_update_brasilia = last_update.astimezone(brasilia_tz)

        if hours_since > 24:
            return {
                "has_data": True,
                "timestamp": last_update_brasilia.strftime("%d/%m/%Y às %H:%M"),
                "hours_since": int(hours_since),
                "type": "danger",
                "message": f"⚠️ ATENÇÃO: Dados desatualizados! Última atualização há {int(hours_since)} horas",
            }
        elif hours_since > 6:
            return {
                "has_data": True,
                "timestamp": last_update_brasilia.strftime("%d/%m/%Y às %H:%M"),
                "hours_since": int(hours_since),
                "type": "warning",
                "message": f"⏰ Última atualização há {int(hours_since)} horas",
            }
        else:
            return {
                "has_data": True,
                "timestamp": last_update_brasilia.strftime("%d/%m/%Y às %H:%M"),
                "hours_since": int(hours_since),
                "type": "success",
                "message": f"✅ Dados atualizados há {int(hours_since)} horas",
            }
