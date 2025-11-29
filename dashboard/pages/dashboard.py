"""Dashboard page - visão geral de produtos, open box e voos."""

import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime
import yaml


def render():
    """Render dashboard page."""

    st.header("📊 Dashboard de Monitoramento")

    # Métricas gerais
    render_metrics()

    st.divider()

    # Alertas ativos
    render_active_alerts()

    # Seções colapsáveis
    with st.expander("🛒 **Produtos Monitorados**", expanded=True):
        render_products_section()

    with st.expander("📦 **Open Box Disponíveis**", expanded=False):
        render_openbox_section()

    with st.expander("✈️ **Monitoramento de Voos**", expanded=False):
        render_flights_section()

    with st.expander("📈 **Gráficos e Tendências**", expanded=False):
        render_charts_section()


def render_metrics():
    """Render top-level metrics."""
    col1, col2, col3, col4 = st.columns(4)

    # Carregar dados
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
        products = config.get("products", [])
        enabled_products = [p for p in products if p.get("enabled", True)]
    else:
        enabled_products = []

    with col1:
        st.metric("📦 Produtos Ativos", len(enabled_products))

    with col2:
        # Contar URLs totais
        total_urls = sum(len(p.get("urls", [])) for p in enabled_products)
        st.metric("🔗 Total de URLs", total_urls)

    with col3:
        # Contar categorias únicas
        categories = set(p.get("category") for p in enabled_products if p.get("category"))
        st.metric("📂 Categorias", len(categories))

    with col4:
        # Última atualização
        history_path = Path("data/price_history.csv")
        if history_path.exists():
            df = pd.read_csv(history_path)
            if not df.empty:
                last_check = pd.to_datetime(df["timestamp"]).max()
                hours_ago = (datetime.now() - last_check).total_seconds() / 3600
                st.metric("🕐 Última Verificação", f"há {hours_ago:.0f}h")
            else:
                st.metric("🕐 Última Verificação", "Nunca")
        else:
            st.metric("🕐 Última Verificação", "Nunca")


def render_active_alerts():
    """Render active price alerts."""
    alert_history_path = Path("data/alert_history.csv")
    if not alert_history_path.exists():
        return

    df = pd.read_csv(alert_history_path)
    if df.empty:
        return

    # Alertas das últimas 24h
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    recent_alerts = df[df["timestamp"] > (datetime.now() - pd.Timedelta(hours=24))]

    if not recent_alerts.empty:
        st.info(f"🔔 **{len(recent_alerts)} alertas enviados nas últimas 24h**")


def render_products_section():
    """Render products monitoring section."""
    st.subheader("Produtos em Monitoramento")

    history_path = Path("data/price_history.csv")
    if not history_path.exists():
        st.warning("Nenhum histórico de preços encontrado. Execute o monitor primeiro.")
        return

    df = pd.read_csv(history_path)
    if df.empty:
        st.warning("Histórico vazio.")
        return

    # Pegar preços mais recentes
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby(["product_id", "store"]).tail(1)

    # Exibir tabela
    display_df = latest[["product_name", "store", "price", "in_stock", "timestamp"]]
    display_df = display_df.sort_values(["product_name", "price"])

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_openbox_section():
    """Render open box section."""
    st.subheader("Open Box Disponíveis")

    openbox_path = Path("data/openbox_history.csv")
    if not openbox_path.exists():
        st.info("Nenhum Open Box detectado ainda.")
        return

    df = pd.read_csv(openbox_path)
    if df.empty:
        st.info("Nenhum Open Box no histórico.")
        return

    # Mostrar os mais recentes
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    recent = df.sort_values("timestamp", ascending=False).head(20)

    st.dataframe(recent[["product_name", "price", "original_price", "discount_percent", "url"]], use_container_width=True, hide_index=True)


def render_flights_section():
    """Render flights section."""
    st.subheader("Voos Monitorados")

    flight_path = Path("data/flight_history.csv")
    if not flight_path.exists():
        st.info("Nenhum voo monitorado ainda.")
        return

    df = pd.read_csv(flight_path)
    if df.empty:
        st.info("Histórico de voos vazio.")
        return

    # Mostrar voos mais recentes
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    recent = df.sort_values("timestamp", ascending=False).head(20)

    st.dataframe(recent[["origin", "destination", "departure_date", "price", "airline", "stops"]], use_container_width=True, hide_index=True)


def render_charts_section():
    """Render price charts."""
    st.subheader("Tendências de Preço")

    history_path = Path("data/price_history.csv")
    if not history_path.exists():
        st.warning("Nenhum histórico disponível para gráficos.")
        return

    df = pd.read_csv(history_path)
    if df.empty:
        st.warning("Histórico vazio.")
        return

    # Selecionar produto para visualizar
    products = df["product_id"].unique()
    selected = st.selectbox("Selecione um produto:", products)

    if selected:
        product_df = df[df["product_id"] == selected].copy()
        product_df["timestamp"] = pd.to_datetime(product_df["timestamp"])
        product_df = product_df.sort_values("timestamp")

        # Chart de linha
        chart_df = product_df[["timestamp", "price", "store"]]
        st.line_chart(chart_df.pivot(index="timestamp", columns="store", values="price"))
