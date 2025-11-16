"""Monitor de Preços - Professional Edition - Aplicação Reflex."""

from __future__ import annotations

import reflex as rx
import pandas as pd

from .state import PriceMonitorState
from .styles import (
    COLORS,
    GRADIENTS,
    CONTAINER_STYLE,
    HEADER_STYLE,
    CARD_STYLE,
    TYPOGRAPHY,
    CATEGORY_EMOJIS,
)
from .components.cards import metric_card, product_card, highlight_card, stat_card
from .components.alerts import alert_banner, data_staleness_banner, loading_spinner, empty_state
from .components.badges import badge, status_badge, category_badge, store_badge, price_trend_badge
from .components.buttons import primary_button, secondary_button, link_button, icon_button


# ============================================================
# HEADER
# ============================================================


def header() -> rx.Component:
    """Header profissional com gradiente."""

    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading(
                    "📉 Monitor de Preços",
                    size="9",
                    font_weight="bold",
                ),
                rx.text(
                    "Professional Edition - Sistema avançado de monitoramento e gestão de preços",
                    font_size="1.1rem",
                    opacity="0.95",
                ),
                spacing="2",
                align="center",
            ),
            max_width="1400px",
        ),
        **HEADER_STYLE,
    )


# ============================================================
# NAVEGAÇÃO (TABS)
# ============================================================


def navigation() -> rx.Component:
    """Barra de navegação com tabs."""

    return rx.box(
        rx.container(
            rx.hstack(
                rx.button(
                    "📊 Dashboard",
                    on_click=PriceMonitorState.set_current_tab("dashboard"),
                    bg=rx.cond(
                        PriceMonitorState.current_tab == "dashboard",
                        GRADIENTS["primary"],
                        COLORS["gray_100"],
                    ),
                    color=rx.cond(
                        PriceMonitorState.current_tab == "dashboard",
                        "white",
                        COLORS["gray_700"],
                    ),
                    border_radius="8px",
                    padding="0.75rem 1.5rem",
                    font_weight="600",
                    _hover={"transform": "translateY(-2px)"},
                ),
                rx.button(
                    "⚙️ Gerenciamento",
                    on_click=PriceMonitorState.set_current_tab("manage"),
                    bg=rx.cond(
                        PriceMonitorState.current_tab == "manage",
                        GRADIENTS["primary"],
                        COLORS["gray_100"],
                    ),
                    color=rx.cond(
                        PriceMonitorState.current_tab == "manage",
                        "white",
                        COLORS["gray_700"],
                    ),
                    border_radius="8px",
                    padding="0.75rem 1.5rem",
                    font_weight="600",
                    _hover={"transform": "translateY(-2px)"},
                ),
                rx.button(
                    "📈 Estatísticas",
                    on_click=PriceMonitorState.set_current_tab("stats"),
                    bg=rx.cond(
                        PriceMonitorState.current_tab == "stats",
                        GRADIENTS["primary"],
                        COLORS["gray_100"],
                    ),
                    color=rx.cond(
                        PriceMonitorState.current_tab == "stats",
                        "white",
                        COLORS["gray_700"],
                    ),
                    border_radius="8px",
                    padding="0.75rem 1.5rem",
                    font_weight="600",
                    _hover={"transform": "translateY(-2px)"},
                ),
                rx.button(
                    "✈️ Voos",
                    on_click=PriceMonitorState.set_current_tab("flights"),
                    bg=rx.cond(
                        PriceMonitorState.current_tab == "flights",
                        GRADIENTS["primary"],
                        COLORS["gray_100"],
                    ),
                    color=rx.cond(
                        PriceMonitorState.current_tab == "flights",
                        "white",
                        COLORS["gray_700"],
                    ),
                    border_radius="8px",
                    padding="0.75rem 1.5rem",
                    font_weight="600",
                    _hover={"transform": "translateY(-2px)"},
                ),
                rx.button(
                    "ℹ️ Sobre",
                    on_click=PriceMonitorState.set_current_tab("about"),
                    bg=rx.cond(
                        PriceMonitorState.current_tab == "about",
                        GRADIENTS["primary"],
                        COLORS["gray_100"],
                    ),
                    color=rx.cond(
                        PriceMonitorState.current_tab == "about",
                        "white",
                        COLORS["gray_700"],
                    ),
                    border_radius="8px",
                    padding="0.75rem 1.5rem",
                    font_weight="600",
                    _hover={"transform": "translateY(-2px)"},
                ),
                spacing="3",
                wrap="wrap",
                justify="center",
            ),
            max_width="1400px",
        ),
        background=COLORS["bg_secondary"],
        padding="1rem",
        box_shadow="0 2px 4px rgba(0, 0, 0, 0.05)",
        margin_bottom="2rem",
    )


# ============================================================
# SIDEBAR (Filtros e Ações)
# ============================================================


def sidebar() -> rx.Component:
    """Sidebar com filtros e ações."""

    return rx.box(
        rx.vstack(
            # Header da sidebar
            rx.heading("⚙️ Configurações", size="6", margin_bottom="1rem"),

            rx.divider(),

            # Filtros
            rx.heading("🔍 Filtros", size="4", margin_top="1rem", margin_bottom="0.5rem"),

            rx.vstack(
                rx.text("Categoria", font_weight="600", font_size="0.9rem"),
                rx.select(
                    ["Todas", "cpu", "gpu", "motherboard", "memory", "storage", "psu", "cooler", "case", "cruise"],
                    value=PriceMonitorState.selected_category,
                    on_change=PriceMonitorState.set_selected_category,
                    width="100%",
                ),

                rx.text("Lojas", font_weight="600", font_size="0.9rem", margin_top="1rem"),
                rx.checkbox("Todas", is_checked="Todas" in PriceMonitorState.selected_stores),
                rx.checkbox("Kabum", is_checked="kabum" in PriceMonitorState.selected_stores),
                rx.checkbox("Amazon", is_checked="amazon" in PriceMonitorState.selected_stores),
                rx.checkbox("Pichau", is_checked="pichau" in PriceMonitorState.selected_stores),

                spacing="2",
                width="100%",
                align_items="start",
            ),

            rx.divider(margin_top="1rem"),

            # Ações
            rx.heading("🔄 Ações", size="4", margin_top="1rem", margin_bottom="0.5rem"),

            rx.vstack(
                rx.button(
                    "🔄 Atualizar Preços",
                    on_click=PriceMonitorState.collect_prices,
                    bg=GRADIENTS["primary"],
                    color="white",
                    width="100%",
                    border_radius="8px",
                    padding="0.75rem",
                    font_weight="600",
                    is_loading=PriceMonitorState.is_collecting,
                ),

                rx.cond(
                    PriceMonitorState.collection_progress,
                    rx.text(
                        PriceMonitorState.collection_progress,
                        font_size="0.85rem",
                        color=COLORS["gray_500"],
                        text_align="center",
                    ),
                    rx.fragment(),
                ),

                spacing="3",
                width="100%",
            ),

            spacing="3",
            width="100%",
            align_items="stretch",
        ),
        **CARD_STYLE,
        width="300px",
        height="fit-content",
        position="sticky",
        top="20px",
    )


# ============================================================
# DASHBOARD - MÉTRICAS PRINCIPAIS
# ============================================================


def dashboard_metrics() -> rx.Component:
    """Métricas principais do dashboard."""

    return rx.grid(
        metric_card(
            "📦 Produtos Ativos",
            PriceMonitorState.active_products,
        ),
        metric_card(
            "🏪 Total de URLs",
            PriceMonitorState.total_urls,
        ),
        metric_card(
            "🔍 Verificações",
            PriceMonitorState.total_checks,
        ),
        metric_card(
            f"💰 Economia Total",
            f"R$ {PriceMonitorState.total_savings:.2f}",
            delta=f"{PriceMonitorState.products_below_target} produtos" if PriceMonitorState.products_below_target > 0 else None,
        ),
        columns="4",
        spacing="4",
        width="100%",
        margin_bottom="2rem",
    )


# ============================================================
# DASHBOARD - DESTAQUES
# ============================================================


def dashboard_highlights() -> rx.Component:
    """Seção de destaques do dashboard."""

    return rx.vstack(
        rx.heading("⭐ Melhores Ofertas do Momento", size="7", margin_bottom="1rem"),

        # TODO: Aqui vamos adicionar:
        # - Produtos abaixo da meta
        # - Quedas de preço
        # - Melhores por categoria
        # - Gráficos

        rx.text("Dashboard de destaques em desenvolvimento..."),

        spacing="4",
        width="100%",
    )


# ============================================================
# DASHBOARD - CATÁLOGO
# ============================================================


def dashboard_catalog() -> rx.Component:
    """Catálogo completo de produtos."""

    return rx.vstack(
        rx.heading("📚 Catálogo Completo", size="7", margin_bottom="1rem"),

        # Filtros de busca
        rx.hstack(
            rx.input(
                placeholder="🔍 Buscar produto...",
                value=PriceMonitorState.search_term,
                on_change=PriceMonitorState.set_search_term,
                flex="1",
            ),
            rx.select(
                ["Menor preço", "Maior preço", "Nome (A-Z)", "Loja"],
                value=PriceMonitorState.sort_by,
                on_change=PriceMonitorState.set_sort_by,
                width="200px",
            ),
            width="100%",
            spacing="3",
        ),

        # TODO: Lista de produtos filtrados

        rx.text("Catálogo em desenvolvimento..."),

        spacing="4",
        width="100%",
    )


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================


def dashboard_page() -> rx.Component:
    """Página principal do dashboard."""

    return rx.vstack(
        rx.heading("📊 Dashboard de Preços", size="8", margin_bottom="1.5rem"),

        # Métricas
        dashboard_metrics(),

        # Banner de atualização
        rx.cond(
            PriceMonitorState.get_last_update_info()["has_data"],
            data_staleness_banner(
                has_data=True,
                timestamp=PriceMonitorState.get_last_update_info()["timestamp"],
                hours_since=PriceMonitorState.get_last_update_info()["hours_since"],
                banner_type=PriceMonitorState.get_last_update_info()["type"],
            ),
            alert_banner("📭 Nenhum dado coletado ainda. Use o botão 'Atualizar Preços'.", "info"),
        ),

        rx.divider(margin_y="2rem"),

        # Tabs internas do dashboard
        rx.hstack(
            rx.button(
                "⭐ Destaques",
                on_click=PriceMonitorState.set_current_dashboard_view("highlights"),
                bg=rx.cond(
                    PriceMonitorState.current_dashboard_view == "highlights",
                    COLORS["primary"],
                    COLORS["gray_200"],
                ),
                color=rx.cond(
                    PriceMonitorState.current_dashboard_view == "highlights",
                    "white",
                    COLORS["gray_700"],
                ),
            ),
            rx.button(
                "📚 Catálogo",
                on_click=PriceMonitorState.set_current_dashboard_view("catalog"),
                bg=rx.cond(
                    PriceMonitorState.current_dashboard_view == "catalog",
                    COLORS["primary"],
                    COLORS["gray_200"],
                ),
                color=rx.cond(
                    PriceMonitorState.current_dashboard_view == "catalog",
                    "white",
                    COLORS["gray_700"],
                ),
            ),
            spacing="3",
            margin_bottom="2rem",
        ),

        # Conteúdo baseado na visualização selecionada
        rx.cond(
            PriceMonitorState.current_dashboard_view == "highlights",
            dashboard_highlights(),
            dashboard_catalog(),
        ),

        spacing="4",
        width="100%",
    )


# ============================================================
# PÁGINA DE GERENCIAMENTO
# ============================================================


def manage_page() -> rx.Component:
    """Página de gerenciamento de produtos."""

    return rx.vstack(
        rx.heading("⚙️ Gerenciamento de Produtos", size="8", margin_bottom="1.5rem"),

        rx.text("Página de gerenciamento em desenvolvimento..."),

        # TODO: Implementar CRUD de produtos

        spacing="4",
        width="100%",
    )


# ============================================================
# PÁGINA DE ESTATÍSTICAS
# ============================================================


def stats_page() -> rx.Component:
    """Página de estatísticas."""

    return rx.vstack(
        rx.heading("📈 Estatísticas e Análises", size="8", margin_bottom="1.5rem"),

        # Métricas gerais
        rx.grid(
            metric_card("📦 Total de Produtos", PriceMonitorState.total_products),
            metric_card("✅ Ativos", PriceMonitorState.active_products),
            metric_card("❌ Inativos", PriceMonitorState.total_products - PriceMonitorState.active_products),
            metric_card("🔗 Total de URLs", PriceMonitorState.total_urls),
            columns="4",
            spacing="4",
            width="100%",
        ),

        rx.divider(margin_y="2rem"),

        rx.text("Estatísticas detalhadas em desenvolvimento..."),

        spacing="4",
        width="100%",
    )


# ============================================================
# PÁGINA DE VOOS
# ============================================================


def flights_page() -> rx.Component:
    """Página de monitoramento de voos."""

    return rx.vstack(
        rx.heading("✈️ Monitor de Voos", size="8", margin_bottom="1.5rem"),

        rx.hstack(
            rx.button(
                "🔍 Buscar Voos",
                on_click=PriceMonitorState.collect_flights,
                bg=GRADIENTS["primary"],
                color="white",
                is_loading=PriceMonitorState.is_loading,
            ),
            rx.text(
                "💡 A busca usa IA e pode demorar ~5 minutos",
                color=COLORS["gray_500"],
            ),
            spacing="3",
        ),

        rx.divider(margin_y="2rem"),

        rx.text("Painel de voos em desenvolvimento..."),

        spacing="4",
        width="100%",
    )


# ============================================================
# PÁGINA SOBRE
# ============================================================


def about_page() -> rx.Component:
    """Página sobre o sistema."""

    return rx.vstack(
        rx.heading("ℹ️ Sobre o Sistema", size="8", margin_bottom="1.5rem"),

        rx.box(
            rx.vstack(
                rx.heading("📉 Monitor de Preços - Professional Edition", size="6"),
                rx.text(
                    "Sistema profissional e completo de monitoramento de preços com recursos avançados.",
                    margin_top="1rem",
                ),

                rx.heading("🎯 Funcionalidades Premium:", size="5", margin_top="2rem"),
                rx.unordered_list(
                    rx.list_item("✅ Visualização de preços em tempo real"),
                    rx.list_item("✅ Gráficos e estatísticas interativas"),
                    rx.list_item("✅ Filtros avançados (categoria, loja, preço)"),
                    rx.list_item("✅ Gerenciamento completo de produtos"),
                    rx.list_item("✅ Import/Export (CSV/JSON)"),
                    rx.list_item("✅ Monitor de voos"),
                    rx.list_item("✅ Alertas por email"),
                    margin_top="1rem",
                ),

                rx.heading("🛠️ Lojas Suportadas:", size="5", margin_top="2rem"),
                rx.hstack(
                    store_badge("kabum"),
                    store_badge("amazon"),
                    store_badge("pichau"),
                    store_badge("mercadolivre"),
                    spacing="3",
                    margin_top="1rem",
                ),

                rx.divider(margin_y="2rem"),

                rx.hstack(
                    rx.text("Versão: 4.0.0 (Reflex Professional Edition)", font_weight="600"),
                    rx.text("•"),
                    rx.text("Status: ✅ Produção"),
                    spacing="2",
                ),

                spacing="3",
                align_items="start",
            ),
            **CARD_STYLE,
        ),

        spacing="4",
        width="100%",
    )


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================


def main_layout() -> rx.Component:
    """Layout principal da aplicação."""

    return rx.vstack(
        # Header
        header(),

        # Navegação
        navigation(),

        # Conteúdo principal
        rx.container(
            rx.hstack(
                # Sidebar (somente no dashboard)
                rx.cond(
                    PriceMonitorState.current_tab == "dashboard",
                    sidebar(),
                    rx.fragment(),
                ),

                # Conteúdo da página
                rx.box(
                    # Mensagens de erro/sucesso
                    rx.cond(
                        PriceMonitorState.error_message,
                        alert_banner(PriceMonitorState.error_message, "danger"),
                        rx.fragment(),
                    ),
                    rx.cond(
                        PriceMonitorState.success_message,
                        alert_banner(PriceMonitorState.success_message, "success"),
                        rx.fragment(),
                    ),

                    # Páginas
                    rx.cond(
                        PriceMonitorState.current_tab == "dashboard",
                        dashboard_page(),
                        rx.cond(
                            PriceMonitorState.current_tab == "manage",
                            manage_page(),
                            rx.cond(
                                PriceMonitorState.current_tab == "stats",
                                stats_page(),
                                rx.cond(
                                    PriceMonitorState.current_tab == "flights",
                                    flights_page(),
                                    about_page(),
                                ),
                            ),
                        ),
                    ),

                    flex="1",
                ),

                spacing="6",
                align_items="start",
                width="100%",
            ),
            max_width="1400px",
        ),

        spacing="0",
        width="100%",
        min_height="100vh",
        background=COLORS["bg_secondary"],
    )


# ============================================================
# APLICAÇÃO
# ============================================================


def index() -> rx.Component:
    """Página inicial que carrega dados."""

    return rx.fragment(
        main_layout(),
        on_mount=PriceMonitorState.on_load,
    )


# Criar aplicação
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="indigo",
    ),
)

app.add_page(index, route="/", title="Monitor de Preços - Professional Edition")
