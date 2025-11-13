from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from src.price_monitor import PriceMonitor
from src.flight_monitor import FlightMonitor

logging.basicConfig(level=logging.INFO)

CONFIG_PATH = Path("config/products.yaml")
HISTORY_PATH = Path("data/price_history.csv")
FLIGHT_CONFIG_PATH = Path("config/flights.yaml")
FLIGHT_HISTORY_PATH = Path("data/flight_history.csv")

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

# Filtrar apenas produtos que ainda existem no config
history_df = history_df[history_df["product_id"].isin(products.keys())]

latest_df = (
    history_df.sort_values("timestamp")
    .groupby(["product_id", "store"])
    .tail(1)
    .reset_index(drop=True)
)

latest_df["status"] = latest_df.apply(
    lambda row: "Abaixo da meta" if (
        pd.notna(row["price"])
        and row["product_id"] in products
        and pd.notna(products[row["product_id"]].desired_price)
        and row["price"] <= products[row["product_id"]].desired_price
    )
    else "Acima da meta" if row["product_id"] in products else "Produto removido",
    axis=1,
)

# Calcular variação de preço (comparar com penúltimo registro)
def calculate_price_trend(row):
    """Calcula tendência de preço: subiu (🔴), estável (🟡), desceu (🟢)"""
    try:
        # Verificar se produto ainda existe no config
        if row["product_id"] not in products:
            return "⚪ Removido"
        
        product_history = history_df[
            (history_df["product_id"] == row["product_id"]) &
            (history_df["store"] == row["store"]) &
            (history_df["price"].notna())
        ].sort_values("timestamp")
        
        if len(product_history) < 2:
            return "🟡 Novo"  # Primeiro registro
        
        current_price = row["price"]
        previous_price = product_history.iloc[-2]["price"]
        
        if pd.isna(current_price) or pd.isna(previous_price):
            return "⚪ N/A"
        
        diff = current_price - previous_price
        diff_percent = (diff / previous_price) * 100
        
        if diff_percent > 1:  # Subiu mais de 1%
            return f"🔴 +R$ {diff:.2f} (+{diff_percent:.1f}%)"
        elif diff_percent < -1:  # Caiu mais de 1%
            return f"🟢 R$ {diff:.2f} ({diff_percent:.1f}%)"
        else:  # Estável (variação < 1%)
            return f"🟡 Estável ({diff_percent:.1f}%)"
    except Exception as e:
        return "⚪ N/A"

latest_df["tendencia"] = latest_df.apply(calculate_price_trend, axis=1)

st.subheader("Panorama atual")

# Configurar coluna de URL como link clicável
display_df = latest_df[
    [
        "product_name",
        "store",
        "raw_price",
        "price",
        "tendencia",
        "currency",
        "in_stock",
        "status",
        "timestamp",
        "url",
    ]
].copy()

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "product_name": st.column_config.TextColumn(
            "Produto",
            width="large"
        ),
        "store": st.column_config.TextColumn(
            "Loja",
            width="small"
        ),
        "raw_price": st.column_config.TextColumn(
            "Preço Original",
            width="small"
        ),
        "price": st.column_config.NumberColumn(
            "Preço",
            format="R$ %.2f"
        ),
        "tendencia": st.column_config.TextColumn(
            "Tendência",
            help="🔴 Subiu | 🟡 Estável | 🟢 Caiu",
            width="medium"
        ),
        "timestamp": st.column_config.DatetimeColumn(
            "Atualizado",
            format="DD/MM/YY HH:mm"
        ),
        "url": st.column_config.LinkColumn(
            "Ver Oferta",
            help="Clique para abrir a página do produto (1 clique)",
            validate="^https?://",
            max_chars=100,
        ),
    }
)

# Botões diretos para mobile (alternativa mais fácil)
with st.expander("📱 Links Diretos (melhor para celular - 1 clique)", expanded=False):
    for idx, row in display_df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{row['product_name']}** ({row['store']})")
        with col2:
            st.write(f"R$ {row['price']:.2f}")
        with col3:
            st.link_button("🔗 Abrir", row['url'], use_container_width=True)

# Gráfico de variação percentual - Últimas 24h
st.subheader("📊 Variação Percentual - Últimas 24h")

last_24h = history_df[
    (history_df['timestamp'] > (datetime.now(timezone.utc) - timedelta(hours=24))) &
    (history_df['price'].notna())
]

if not last_24h.empty:
    variations = []
    # Filtrar apenas produtos que existem no config
    valid_product_ids = set(products.keys()) & set(last_24h['product_id'].unique())
    for product_id in valid_product_ids:
        product_data = last_24h[last_24h['product_id'] == product_id]
        if len(product_data) >= 2:
            # Pegar primeiro e último preço
            product_data_sorted = product_data.sort_values('timestamp')
            first_price = product_data_sorted.iloc[0]['price']
            last_price = product_data_sorted.iloc[-1]['price']
            
            if pd.notna(first_price) and pd.notna(last_price) and first_price > 0:
                variation = ((last_price - first_price) / first_price) * 100
                variations.append({
                    'Produto': products[product_id].name if product_id in products else f"Produto {product_id} (removido)",
                    'Variação (%)': round(variation, 2),
                    'Status': '📈' if variation > 0 else '📉' if variation < 0 else '➡️'
                })
    
    if variations:
        var_df = pd.DataFrame(variations)
        var_df = var_df.sort_values('Variação (%)')
        
        # Gráfico de barras
        st.bar_chart(var_df.set_index('Produto')['Variação (%)'], height=300)
        
        # Tabela com detalhes
        with st.expander("📋 Ver detalhes das variações"):
            st.dataframe(var_df, use_container_width=True, hide_index=True)
    else:
        st.info("Não há dados suficientes para calcular variações nas últimas 24h")
else:
    st.info("Não há dados coletados nas últimas 24h")

st.subheader("Histórico de preços")

if product_options:
    selected_history_products = st.multiselect(
        "Selecione produtos para visualizar o histórico",
        options=list(product_options.keys()),
        default=list(product_options.keys())[:3] if len(product_options) >= 3 else list(product_options.keys()),
    )
else:
    selected_history_products = []

if selected_history_products:
    selected_ids = [product_options[name] for name in selected_history_products]
    # Filtrar apenas IDs que existem no histórico e no config
    valid_ids = [pid for pid in selected_ids if pid in products and pid in history_df["product_id"].values]
    filtered_history = history_df[history_df["product_id"].isin(valid_ids)] if valid_ids else pd.DataFrame()

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

# ============================================================
# SEÇÃO DE VOOS
# ============================================================

st.markdown("---")
st.header("✈️ Monitor de Voos")

# Botão para buscar voos
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔍 Buscar Voos Agora", help="Busca voos usando DeepSeek AI (pode demorar alguns minutos)"):
        with st.spinner("Buscando voos... Isso pode levar alguns minutos..."):
            try:
                flight_monitor = FlightMonitor(
                    config_path=FLIGHT_CONFIG_PATH,
                    history_path=FLIGHT_HISTORY_PATH
                )
                flights = flight_monitor.collect()
                flight_monitor.close()
                st.success(f"✅ Encontrados {len(flights)} voos!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao buscar voos: {e}")

with col2:
    st.info("💡 A busca de voos usa IA (DeepSeek) e pode demorar ~5 minutos. Configure em `config/flights.yaml`")

# Mostrar voos salvos
if FLIGHT_HISTORY_PATH.exists():
    try:
        flight_monitor_display = FlightMonitor(
            config_path=FLIGHT_CONFIG_PATH,
            history_path=FLIGHT_HISTORY_PATH
        )
        flights_df = flight_monitor_display.get_latest_flights()
        
        if not flights_df.empty:
            st.subheader("🎫 Melhores Voos Encontrados")
            
            # Calcular tendência de preço para voos
            def calculate_flight_trend(row):
                """Calcula tendência de preço de voo"""
                try:
                    # Buscar histórico completo do voo
                    flight_history_df = pd.read_csv(FLIGHT_HISTORY_PATH, encoding="utf-8")
                    flight_history_df["timestamp"] = pd.to_datetime(flight_history_df["timestamp"])
                    
                    flight_hist = flight_history_df[
                        (flight_history_df["origin"] == row["origin"]) &
                        (flight_history_df["destination"] == row["destination"]) &
                        (flight_history_df["departure_date"] == row["departure_date"]) &
                        (flight_history_df["return_date"] == row["return_date"]) &
                        (flight_history_df["airline"] == row["airline"])
                    ].sort_values("timestamp")
                    
                    if len(flight_hist) < 2:
                        return "🟡 Novo"
                    
                    current = row["price"]
                    previous = flight_hist.iloc[-2]["price"]
                    diff = current - previous
                    diff_percent = (diff / previous) * 100
                    
                    if diff_percent > 2:
                        return f"🔴 +R$ {diff:.0f}"
                    elif diff_percent < -2:
                        return f"🟢 R$ {diff:.0f}"
                    else:
                        return "🟡 Estável"
                except:
                    return "🟡 Novo"
            
            flights_df["tendencia"] = flights_df.apply(calculate_flight_trend, axis=1)
            
            # Formatar para exibição
            display_df = flights_df[[
                "airline",
                "origin",
                "destination",
                "departure_date",
                "return_date",
                "price",
                "tendencia",
                "stops",
                "duration",
                "url"
            ]].copy()
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "airline": st.column_config.TextColumn("Companhia", width="medium"),
                    "origin": st.column_config.TextColumn("Origem", width="small"),
                    "destination": st.column_config.TextColumn("Destino", width="small"),
                    "departure_date": st.column_config.DateColumn("Ida", format="DD/MM/YYYY"),
                    "return_date": st.column_config.DateColumn("Volta", format="DD/MM/YYYY"),
                    "price": st.column_config.NumberColumn("Preço", format="R$ %.0f"),
                    "tendencia": st.column_config.TextColumn(
                        "Tendência",
                        help="🔴 Subiu | 🟡 Estável | 🟢 Caiu",
                        width="small"
                    ),
                    "stops": st.column_config.NumberColumn("Paradas", width="small"),
                    "duration": st.column_config.TextColumn("Duração", width="small"),
                    "url": st.column_config.LinkColumn(
                        "Link",
                        help="Clique para abrir no Google Flights",
                        display_text="🔗 Ver"
                    ),
                }
            )
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Menor Preço", f"R$ {flights_df['price'].min():.2f}")
            with col2:
                st.metric("📊 Preço Médio", f"R$ {flights_df['price'].mean():.2f}")
            with col3:
                st.metric("✈️ Total de Opções", len(flights_df))
        else:
            st.info("📭 Nenhum voo encontrado ainda. Clique em 'Buscar Voos Agora' para começar!")
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar voos: {e}")
else:
    st.info("📭 Nenhum voo monitorado ainda. Configure em `config/flights.yaml` e clique em 'Buscar Voos Agora'!")

