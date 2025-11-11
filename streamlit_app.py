from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.price_monitor import PriceMonitor

logging.basicConfig(level=logging.INFO)

CONFIG_PATH = Path("config/products.yaml")
HISTORY_PATH = Path("data/price_history.csv")

st.set_page_config(page_title="Monitor de Preços - Black Friday", layout="wide")

st.title("📉 Monitor de Preços da Black Friday")

st.session_state.setdefault("auto_refresh_enabled", True)
st.session_state.setdefault("auto_refresh_interval", 5)

monitor = PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)
products = monitor.products


def inject_auto_refresh(enabled: bool, interval_minutes: float) -> None:
    if not enabled:
        return
    seconds = max(10, int(interval_minutes * 60))
    st.markdown(
        f"""
        <script>
            const reload = () => window.location.reload();
            setTimeout(reload, {seconds * 1000});
        </script>
        """,
        unsafe_allow_html=True,
    )


def refresh_prices(selected_ids: list[str] | None = None):
    with st.spinner("Coletando preços atualizados..."):
        snapshots = monitor.collect(product_ids=selected_ids)
    st.success(f"Coleta finalizada com {len(snapshots)} registros.")


with st.sidebar:
    st.header("Configurações")
    product_options = {prod.name: prod.id for prod in products.values()}
    selected_products = st.multiselect(
        "Produtos para atualizar agora",
        options=list(product_options.keys()),
    )

    if st.button("Atualizar preços agora", type="primary"):
        ids = [product_options[name] for name in selected_products] if selected_products else None
        refresh_prices(ids)

    st.markdown("---")
    st.subheader("Categorias")
    selected_category = st.selectbox(
        "Filtrar por categoria",
        options=["Todas"] + sorted(monitor.available_categories()),
        index=0,
    )

    st.markdown("---")
    auto_refresh = st.toggle(
        "Atualização automática",
        value=st.session_state["auto_refresh_enabled"],
        help="Força o dashboard a recarregar a cada intervalo configurado.",
        key="auto_refresh_toggle",
    )
    st.session_state["auto_refresh_enabled"] = auto_refresh

    refresh_interval = st.number_input(
        "Intervalo de auto atualização (minutos)",
        min_value=0.2,
        max_value=120.0,
        value=float(st.session_state["auto_refresh_interval"]),
        help="Defina 0.2 para ~12 segundos.",
    )
    st.session_state["auto_refresh_interval"] = refresh_interval

    st.markdown("---")
    st.caption(
        "⚠️ Respeite os termos de uso das lojas e evite executar coletas com alta frequência. "
        "Use os filtros para focar nos produtos de maior interesse."
    )

inject_auto_refresh(
    st.session_state["auto_refresh_enabled"],
    st.session_state["auto_refresh_interval"],
)

history_df = monitor.load_history()

if history_df.empty:
    st.info("Nenhum dado coletado ainda. Use o botão de atualizar preços na barra lateral.")
    st.stop()

history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)

if selected_category != "Todas":
    history_df = history_df[history_df["category"] == selected_category]

latest_df = (
    history_df.sort_values("timestamp")
    .groupby(["product_id", "store"])
    .tail(1)
    .reset_index(drop=True)
)

latest_df["status"] = latest_df.apply(
    lambda row: "Abaixo da meta" if pd.notna(row["price"])
    and pd.notna(products[row["product_id"]].desired_price)
    and row["price"] <= products[row["product_id"]].desired_price
    else "Acima da meta",
    axis=1,
)

st.subheader("Panorama atual")

st.dataframe(
    latest_df[
        [
            "product_name",
            "store",
            "raw_price",
            "price",
            "currency",
            "in_stock",
            "status",
            "timestamp",
            "url",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Histórico de preços")

selected_history_products = st.multiselect(
    "Selecione produtos para visualizar o histórico",
    options=list(product_options.keys()),
    default=list(product_options.keys())[:3],
)

if selected_history_products:
    selected_ids = [product_options[name] for name in selected_history_products]
    filtered_history = history_df[history_df["product_id"].isin(selected_ids)]

    chart_data = (
        filtered_history.dropna(subset=["price"])
        .pivot_table(
            index="timestamp",
            columns="product_name",
            values="price",
        )
        .sort_index()
    )

    if not chart_data.empty:
        st.line_chart(chart_data)
    else:
        st.warning("Ainda não há dados numéricos suficientes para gerar o gráfico.")

st.subheader("Últimos eventos")
history_df["timestamp_local"] = history_df["timestamp"].dt.tz_convert("America/Sao_Paulo")
history_df["timestamp_fmt"] = history_df["timestamp_local"].dt.strftime("%d/%m %H:%M")

recent_events = history_df.sort_values("timestamp", ascending=False).head(20)
recent_events_display = recent_events[
    ["timestamp_fmt", "product_name", "store", "raw_price", "error"]
].rename(
    columns={
        "timestamp_fmt": "Horário",
        "product_name": "Produto",
        "store": "Loja",
        "raw_price": "Preço",
        "error": "Erro",
    }
)

st.table(recent_events_display)

