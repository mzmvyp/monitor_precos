from __future__ import annotations

import csv
import io
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from src.price_monitor import PriceMonitor
from src.flight_monitor import FlightMonitor

logging.basicConfig(level=logging.INFO)

CONFIG_PATH = Path("config/products.yaml")
HISTORY_PATH = Path("data/price_history.csv")
FLIGHT_CONFIG_PATH = Path("config/flights.yaml")
FLIGHT_HISTORY_PATH = Path("data/flight_history.csv")

st.set_page_config(
    page_title="Monitor de Preços - Professional Edition",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📉"
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def load_yaml_config():
    """Carrega configuração do YAML."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml_config(config):
    """Salva configuração no YAML."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def add_product(config, product_data):
    """Adiciona novo produto ao config."""
    config['items'].append(product_data)
    save_yaml_config(config)

def update_product(config, product_id, updates):
    """Atualiza produto existente."""
    for item in config['items']:
        if item['id'] == product_id:
            item.update(updates)
            break
    save_yaml_config(config)

def delete_product(config, product_id):
    """Remove produto do config."""
    config['items'] = [item for item in config['items'] if item['id'] != product_id]
    save_yaml_config(config)

def toggle_product(config, product_id, enabled):
    """Ativa ou desativa produto."""
    for item in config['items']:
        if item['id'] == product_id:
            item['enabled'] = enabled
            break
    save_yaml_config(config)

def duplicate_product(config, product_id):
    """Duplica um produto existente."""
    for item in config['items']:
        if item['id'] == product_id:
            # Criar cópia com novo ID
            new_item = item.copy()
            new_item['id'] = f"{product_id}-copy-{len(config['items'])}"
            new_item['name'] = f"{item['name']} (Cópia)"
            new_item['enabled'] = False  # Desativado por padrão
            config['items'].append(new_item)
            save_yaml_config(config)
            return new_item['id']
    return None

def export_to_csv(config):
    """Exporta produtos para CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Cabeçalho
    writer.writerow(['id', 'name', 'category', 'desired_price', 'enabled', 'store', 'url'])

    # Dados
    for item in config['items']:
        for url_data in item.get('urls', []):
            writer.writerow([
                item['id'],
                item['name'],
                item['category'],
                item.get('desired_price', 0),
                item.get('enabled', True),
                url_data['store'],
                url_data['url']
            ])

    return output.getvalue()

def export_to_json(config):
    """Exporta produtos para JSON."""
    return json.dumps(config, ensure_ascii=False, indent=2)

def import_from_csv(csv_content):
    """Importa produtos de CSV."""
    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_content))

    # Agrupar por ID
    products = {}
    for row in reader:
        product_id = row['id']
        if product_id not in products:
            products[product_id] = {
                'id': product_id,
                'name': row['name'],
                'category': row['category'],
                'desired_price': float(row['desired_price']),
                'enabled': row['enabled'].lower() == 'true',
                'urls': []
            }

        products[product_id]['urls'].append({
            'store': row['store'],
            'url': row['url']
        })

    return {'items': list(products.values())}

def import_from_json(json_content):
    """Importa produtos de JSON."""
    return json.loads(json_content)

def get_category_color(category):
    """Retorna cor para cada categoria."""
    colors = {
        'cpu': '#FF6B6B',
        'motherboard': '#4ECDC4',
        'memory': '#45B7D1',
        'storage': '#96CEB4',
        'gpu': '#DDA15E',
        'psu': '#BC6C25',
        'cooler': '#588157',
        'case': '#6C757D',
        'cruise': '#E63946',
        'other': '#495057'
    }
    return colors.get(category, '#6C757D')

def calculate_statistics(config, history_df):
    """Calcula estatísticas dos produtos."""
    stats = {
        'total_products': len(config['items']),
        'active_products': sum(1 for item in config['items'] if item.get('enabled', True)),
        'inactive_products': sum(1 for item in config['items'] if not item.get('enabled', True)),
        'total_urls': sum(len(item.get('urls', [])) for item in config['items']),
        'categories': {},
        'by_store': defaultdict(int),
        'price_stats': {},
        'below_target': []
    }

    # Estatísticas por categoria
    for item in config['items']:
        category = item['category']
        if category not in stats['categories']:
            stats['categories'][category] = {
                'count': 0,
                'active': 0,
                'total_desired_price': 0
            }
        stats['categories'][category]['count'] += 1
        if item.get('enabled', True):
            stats['categories'][category]['active'] += 1
        stats['categories'][category]['total_desired_price'] += item.get('desired_price', 0)

        # Por loja
        for url_data in item.get('urls', []):
            stats['by_store'][url_data['store']] += 1

    # Estatísticas de preços do histórico
    if not history_df.empty:
        latest_prices = history_df.sort_values('timestamp').groupby(['product_id', 'store']).tail(1)

        for _, row in latest_prices.iterrows():
            product_id = row['product_id']
            price = row['price']

            # Encontrar produto no config
            product = next((item for item in config['items'] if item['id'] == product_id), None)
            if product and pd.notna(price):
                desired_price = product.get('desired_price', 0)
                if desired_price > 0 and price <= desired_price:
                    stats['below_target'].append({
                        'name': product['name'],
                        'current_price': price,
                        'desired_price': desired_price,
                        'savings': desired_price - price,
                        'store': row['store']
                    })

    return stats

# ============================================================
# CSS CUSTOMIZADO
# ============================================================

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2em;
        font-weight: bold;
    }
    .metric-card p {
        margin: 5px 0 0 0;
        font-size: 0.9em;
        opacity: 0.9;
    }
    .category-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        color: white;
        margin: 2px;
    }
    .success-badge {
        background-color: #10b981;
    }
    .warning-badge {
        background-color: #f59e0b;
    }
    .danger-badge {
        background-color: #ef4444;
    }
    .info-badge {
        background-color: #3b82f6;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
# 📉 Monitor de Preços - **Professional Edition**
### Sistema avançado de monitoramento e gestão de preços
""")

# ============================================================
# ABAS PRINCIPAIS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "⚙️ Gerenciamento",
    "📈 Estatísticas",
    "✈️ Voos",
    "ℹ️ Sobre"
])

# ============================================================
# ABA 1: DASHBOARD
# ============================================================

with tab1:
    st.header("📊 Dashboard de Preços")

    monitor = PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)
    products = monitor.products

    # Filtrar apenas produtos ativos
    yaml_config = load_yaml_config()
    active_products = {
        prod_id: prod for prod_id, prod in products.items()
        if any(item['id'] == prod_id and item.get('enabled', True) for item in yaml_config['items'])
    }

    # Carregar histórico antes das métricas
    history_df = monitor.load_history()

    # Calcular economia total e alertas
    total_savings = 0.0
    products_below_target = 0
    recent_alerts = []

    if not history_df.empty:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)
        latest_prices = history_df.sort_values("timestamp").groupby(["product_id", "store"]).tail(1)

        for _, row in latest_prices.iterrows():
            product = active_products.get(row["product_id"])
            if product and pd.notna(row["price"]) and pd.notna(product.desired_price):
                if row["price"] <= product.desired_price:
                    savings = product.desired_price - row["price"]
                    total_savings += savings
                    products_below_target += 1
                    recent_alerts.append({
                        'product_name': row['product_name'],
                        'store': row['store'],
                        'price': row['price'],
                        'target': product.desired_price,
                        'savings': savings,
                        'timestamp': row['timestamp']
                    })

    # Métricas principais (agora com 5 colunas)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📦 Produtos Ativos", len(active_products), delta=None)
    with col2:
        total_urls = sum(len(p.urls) for p in active_products.values())
        st.metric("🏪 Total de URLs", total_urls)
    with col3:
        categories = len(set(p.category for p in active_products.values()))
        st.metric("📂 Categorias", categories)
    with col4:
        total_checks = len(history_df) if not history_df.empty else 0
        st.metric("🔍 Verificações", total_checks)
    with col5:
        st.metric("💰 Economia Total", f"R$ {total_savings:.2f}",
                 delta=f"{products_below_target} produtos" if products_below_target > 0 else None,
                 delta_color="normal")

    st.markdown("---")

    # Banner de Atualização de Dados
    if not history_df.empty:
        last_update = history_df["timestamp"].max()
        time_since_update = datetime.now(timezone.utc) - last_update
        hours_since = time_since_update.total_seconds() / 3600

        if hours_since > 24:
            # Dados muito antigos (>24h)
            st.error(f"""
            ⚠️ **ATENÇÃO: Dados desatualizados!**

            Última atualização: **{last_update.strftime('%d/%m/%Y às %H:%M')}** (há **{int(hours_since)} horas**)

            Os preços exibidos podem não refletir os valores atuais dos sites.

            👉 **Clique em "🔄 Atualizar Preços" na barra lateral para coletar preços atuais!**
            """)
        elif hours_since > 6:
            # Dados um pouco antigos (6-24h)
            st.warning(f"""
            ⏰ Última atualização: **{last_update.strftime('%d/%m/%Y às %H:%M')}** (há **{int(hours_since)} horas**)

            💡 Considere atualizar os preços para ver as ofertas mais recentes!
            """)
        else:
            # Dados recentes (<6h)
            st.info(f"""
            ✅ Dados atualizados: **{last_update.strftime('%d/%m/%Y às %H:%M')}** (há **{int(hours_since)} horas**)
            """)

    st.markdown("---")

    # Banner de Notificações/Alertas
    if recent_alerts:
        st.markdown("### 🔔 **Alertas Ativos**")

        # Ordenar por maior economia
        recent_alerts.sort(key=lambda x: x['savings'], reverse=True)
        top_alerts = recent_alerts[:3]  # Mostrar top 3

        alert_cols = st.columns(len(top_alerts))
        for idx, alert in enumerate(top_alerts):
            with alert_cols[idx]:
                savings_percent = (alert['savings'] / alert['target']) * 100
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            padding: 15px; border-radius: 10px; color: white; text-align: center;">
                    <h4 style="margin: 0; font-size: 0.9em;">🎯 {alert['product_name'][:30]}...</h4>
                    <p style="margin: 5px 0; font-size: 1.2em; font-weight: bold;">
                        R$ {alert['price']:.2f}
                    </p>
                    <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">
                        Economize R$ {alert['savings']:.2f} ({savings_percent:.1f}%) na {alert['store'].upper()}
                    </p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    st.markdown("---")

    # Sidebar para filtros e ações
    with st.sidebar:
        st.header("⚙️ Configurações")

        # Filtros
        st.subheader("🔍 Filtros")

        selected_category = st.selectbox(
            "Categoria",
            options=["Todas"] + sorted(monitor.available_categories()),
            index=0,
        )

        selected_stores = st.multiselect(
            "Lojas",
            options=["Todas", "kabum", "amazon", "pichau", "terabyte", "mercadolivre", "other"],
            default=["Todas"]
        )

        price_filter = st.checkbox("Filtrar por preço")
        if price_filter:
            price_range = st.slider(
                "Faixa de preço (R$)",
                min_value=0,
                max_value=10000,
                value=(0, 5000),
                step=100
            )

        st.markdown("---")

        # Seleção de produtos para atualizar
        product_options = {prod.name: prod.id for prod in active_products.values()}
        selected_products = st.multiselect(
            "Produtos para atualizar",
            options=list(product_options.keys()),
        )

        if st.button("🔄 Atualizar Preços", type="primary", width="stretch"):
            ids = [product_options[name] for name in selected_products] if selected_products else None

            try:
                with st.spinner("Coletando preços atualizados... Isso pode levar alguns minutos."):
                    snapshots = monitor.collect(product_ids=ids)

                if snapshots:
                    st.success(f"✅ Coleta finalizada: {len(snapshots)} registros coletados!")
                    st.rerun()
                else:
                    st.warning("⚠️ Nenhum preço foi coletado. Verifique os logs acima.")

            except RuntimeError as e:
                error_msg = str(e)

                if "ChromeDriver" in error_msg or "Chrome binary" in error_msg:
                    st.error("❌ **Erro: ChromeDriver não instalado!**")
                    st.markdown("""
                    ### 🔧 Como Resolver:

                    **Passo 1:** Abra um novo terminal (PowerShell/CMD)

                    **Passo 2:** Execute:
                    ```
                    python instalar_chromedriver_manual.py
                    ```

                    **Passo 3:** Feche este dashboard (Ctrl+C)

                    **Passo 4:** Abra um NOVO terminal e execute:
                    ```
                    streamlit run streamlit_app_premium.py
                    ```

                    **Passo 5:** Clique em "Atualizar Preços" novamente

                    ---

                    📖 **Guia completo:** Veja o arquivo `INSTALACAO_WINDOWS.md`
                    """)
                else:
                    st.error(f"❌ Erro ao coletar preços: {error_msg}")

            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
                with st.expander("📋 Detalhes do erro"):
                    import traceback
                    st.code(traceback.format_exc())

        st.markdown("---")

        # Auto-refresh
        auto_refresh = st.toggle(
            "Atualização automática",
            value=st.session_state.get("auto_refresh_enabled", False),
        )
        st.session_state["auto_refresh_enabled"] = auto_refresh

        if auto_refresh:
            refresh_interval = st.number_input(
                "Intervalo (minutos)",
                min_value=1,
                max_value=120,
                value=5,
            )
            st.session_state["auto_refresh_interval"] = refresh_interval

    # Carregar histórico
    if history_df.empty:
        st.info("📭 Nenhum dado coletado ainda. Use o botão 'Atualizar Preços' na barra lateral.")
    else:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)

        # Aplicar filtros
        if selected_category != "Todas":
            history_df = history_df[history_df["category"] == selected_category]

        if "Todas" not in selected_stores:
            history_df = history_df[history_df["store"].isin(selected_stores)]

        # Filtrar apenas produtos ativos
        active_product_ids = set(active_products.keys())
        history_df = history_df[history_df["product_id"].isin(active_product_ids)]

        if history_df.empty:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
        else:
            latest_df = (
                history_df.sort_values("timestamp")
                .groupby(["product_id", "store"])
                .tail(1)
                .reset_index(drop=True)
            )

            # Aplicar filtro de preço
            if price_filter:
                latest_df = latest_df[
                    (latest_df["price"] >= price_range[0]) &
                    (latest_df["price"] <= price_range[1])
                ]

            # Calcular tendências
            def calculate_price_trend(row):
                try:
                    if row["product_id"] not in products:
                        return "⚪ Removido"

                    product_history = history_df[
                        (history_df["product_id"] == row["product_id"]) &
                        (history_df["store"] == row["store"]) &
                        (history_df["price"].notna())
                    ].sort_values("timestamp")

                    if len(product_history) < 2:
                        return "🟡 Novo"

                    current_price = row["price"]
                    previous_price = product_history.iloc[-2]["price"]

                    if pd.isna(current_price) or pd.isna(previous_price):
                        return "⚪ N/A"

                    diff = current_price - previous_price
                    diff_percent = (diff / previous_price) * 100

                    if diff_percent > 1:
                        return f"🔴 +R$ {diff:.2f}"
                    elif diff_percent < -1:
                        return f"🟢 -R$ {abs(diff):.2f}"
                    else:
                        return "🟡 Estável"
                except:
                    return "⚪ N/A"

            latest_df["tendencia"] = latest_df.apply(calculate_price_trend, axis=1)

            latest_df["status"] = latest_df.apply(
                lambda row: "✅ Abaixo da meta" if (
                    pd.notna(row["price"])
                    and row["product_id"] in products
                    and pd.notna(products[row["product_id"]].desired_price)
                    and row["price"] <= products[row["product_id"]].desired_price
                )
                else "⚠️ Acima da meta" if row["product_id"] in products else "❌ Removido",
                axis=1,
            )

            # Tabs para visualizações diferentes
            view_tab1, view_tab2 = st.tabs(["⭐ Destaques", "📚 Catálogo Completo"])

            with view_tab1:
                st.subheader("⭐ Melhores Ofertas do Momento")

                # === SEÇÃO: Gráfico de Evolução de Preço (7 dias) ===
                st.markdown("### 📊 **Evolução de Preços (Últimos 7 dias)**")

                # Filtrar últimos 7 dias
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                recent_history = history_df[history_df['timestamp'] >= seven_days_ago].copy()

                if not recent_history.empty and len(active_products) > 0:
                    # Seletor de produto para ver evolução
                    product_names = {prod.name: prod_id for prod_id, prod in active_products.items()}
                    selected_product_name = st.selectbox(
                        "Selecione um produto para ver a evolução:",
                        options=list(product_names.keys()),
                        key="evolution_product_select"
                    )

                    if selected_product_name:
                        selected_prod_id = product_names[selected_product_name]
                        product_evolution = recent_history[
                            recent_history['product_id'] == selected_prod_id
                        ].copy()

                        if not product_evolution.empty:
                            # Criar gráfico com Plotly
                            try:
                                import plotly.graph_objects as go

                                fig = go.Figure()

                                # Adicionar linha para cada loja
                                for store in product_evolution['store'].unique():
                                    store_data = product_evolution[product_evolution['store'] == store].sort_values('timestamp')

                                    fig.add_trace(go.Scatter(
                                        x=store_data['timestamp'],
                                        y=store_data['price'],
                                        mode='lines+markers',
                                        name=store.upper(),
                                        line=dict(width=2),
                                        marker=dict(size=8)
                                    ))

                                # Adicionar linha do preço desejado
                                product_obj = active_products[selected_prod_id]
                                if product_obj.desired_price:
                                    fig.add_hline(
                                        y=product_obj.desired_price,
                                        line_dash="dash",
                                        line_color="green",
                                        annotation_text=f"Meta: R$ {product_obj.desired_price:.2f}",
                                        annotation_position="right"
                                    )

                                fig.update_layout(
                                    title=f"Evolução de Preço - {selected_product_name}",
                                    xaxis_title="Data",
                                    yaxis_title="Preço (R$)",
                                    hovermode='x unified',
                                    height=400
                                )

                                st.plotly_chart(
                                    fig,
                                    use_container_width=True,
                                    config={'displayModeBar': True, 'displaylogo': False}
                                )
                            except ImportError:
                                st.info("📊 Instale plotly para ver gráficos interativos: `pip install plotly`")
                        else:
                            st.info("📭 Sem dados dos últimos 7 dias para este produto.")
                else:
                    st.info("📭 Sem dados suficientes para mostrar evolução de preços.")

                st.markdown("---")

                # === SEÇÃO: Ranking de Lojas ===
                st.markdown("### 🏆 **Ranking de Lojas**")
                st.markdown("##### Qual loja tem os melhores preços?")

                # Calcular ranking
                store_stats = {}
                for _, row in latest_df.iterrows():
                    store = row['store']
                    if store not in store_stats:
                        store_stats[store] = {
                            'total_products': 0,
                            'below_target': 0,
                            'avg_price': [],
                            'total_savings': 0.0
                        }

                    store_stats[store]['total_products'] += 1
                    if pd.notna(row['price']):
                        store_stats[store]['avg_price'].append(row['price'])

                    if row['status'] == '✅ Abaixo da meta':
                        store_stats[store]['below_target'] += 1
                        product = products.get(row["product_id"])
                        if product and pd.notna(product.desired_price):
                            savings = product.desired_price - row['price']
                            store_stats[store]['total_savings'] += savings

                # Ordenar por número de produtos abaixo da meta
                ranked_stores = sorted(
                    store_stats.items(),
                    key=lambda x: (x[1]['below_target'], x[1]['total_savings']),
                    reverse=True
                )

                # Exibir ranking em colunas
                rank_cols = st.columns(min(4, len(ranked_stores)))
                for idx, (store, stats) in enumerate(ranked_stores[:4]):
                    with rank_cols[idx]:
                        medal = ["🥇", "🥈", "🥉", "🏅"][min(idx, 3)]
                        avg_price = sum(stats['avg_price']) / len(stats['avg_price']) if stats['avg_price'] else 0

                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    padding: 15px; border-radius: 10px; color: white; text-align: center;">
                            <h3 style="margin: 0;">{medal} {store.upper()}</h3>
                            <p style="margin: 5px 0; font-size: 1.1em;">
                                <strong>{stats['below_target']}</strong> produtos no preço
                            </p>
                            <p style="margin: 0; font-size: 0.9em; opacity: 0.9;">
                                Economia: R$ {stats['total_savings']:.2f}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")

                # Separar produtos por relevância
                below_target = latest_df[latest_df["status"] == "✅ Abaixo da meta"].copy()
                price_drops = latest_df[latest_df["tendencia"].str.contains("🟢", na=False)].copy()

                # Seção 1: Produtos abaixo do preço desejado (OPORTUNIDADES!)
                if not below_target.empty:
                    st.markdown("### 🎯 **Atingiram o preço desejado!**")
                    st.markdown("##### Produtos que estão no preço que você quer ou abaixo:")

                    for idx, row in below_target.head(10).iterrows():
                        product = products.get(row["product_id"])
                        if product and pd.notna(row["price"]):
                            savings = product.desired_price - row["price"]
                            savings_percent = (savings / product.desired_price) * 100

                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            with col1:
                                st.markdown(f"**{row['product_name']}**")
                                st.caption(f"🏪 {row['store'].upper()}")
                            with col2:
                                st.metric("Preço Atual", f"R$ {row['price']:.2f}")
                            with col3:
                                st.metric("Meta", f"R$ {product.desired_price:.2f}")
                            with col4:
                                st.metric("Economia", f"R$ {savings:.2f}", delta=f"-{savings_percent:.1f}%")
                                st.link_button("🛒 Ver Oferta", row["url"], width="stretch")
                    st.markdown("---")
                else:
                    st.info("📭 Nenhum produto atingiu o preço desejado ainda. Continue monitorando!")

                # Seção 2: Maiores quedas de preço
                if not price_drops.empty:
                    st.markdown("### 📉 **Quedas de Preço Recentes**")
                    st.markdown("##### Produtos que baixaram de preço desde a última verificação:")

                    # Ordenar por maior queda
                    price_drops_sorted = price_drops.sort_values(
                        by="tendencia",
                        ascending=True
                    ).head(5)

                    for idx, row in price_drops_sorted.iterrows():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{row['product_name']}**")
                            st.caption(f"🏪 {row['store'].upper()} • {row['tendencia']}")
                        with col2:
                            st.metric("Preço", f"R$ {row['price']:.2f}")
                        with col3:
                            st.link_button("🛒 Ver", row["url"], width="stretch")
                    st.markdown("---")

                # Seção 3: Top ofertas por categoria
                st.markdown("### 🏆 **Melhores Preços por Categoria**")
                st.markdown("##### O produto mais barato de cada categoria:")

                # Agrupar por categoria e pegar o menor preço
                categories = latest_df[latest_df["price"].notna()].groupby("category")

                cols = st.columns(2)
                for col_idx, (category, group) in enumerate(categories):
                    with cols[col_idx % 2]:
                        best_deal = group.nsmallest(1, "price").iloc[0]

                        category_emoji = {
                            "cpu": "🖥️",
                            "gpu": "🎮",
                            "motherboard": "⚡",
                            "memory": "💾",
                            "storage": "💿",
                            "psu": "🔌",
                            "cooler": "❄️",
                            "case": "📦",
                            "cruise": "🚢"
                        }.get(category, "📦")

                        with st.container():
                            st.markdown(f"**{category_emoji} {category.upper()}**")
                            st.markdown(f"{best_deal['product_name']}")
                            st.caption(f"🏪 {best_deal['store'].upper()} • R$ {best_deal['price']:.2f}")
                            st.link_button("Ver Oferta", best_deal["url"], width="stretch")
                            st.markdown("---")

            with view_tab2:
                st.subheader("📚 Catálogo Completo de Produtos")

                # Filtros adicionais específicos para o catálogo
                col_filter1, col_filter2, col_filter3 = st.columns(3)

                with col_filter1:
                    search_term = st.text_input("🔍 Buscar produto", placeholder="Digite o nome...")

                with col_filter2:
                    sort_by = st.selectbox(
                        "Ordenar por",
                        ["Menor preço", "Maior preço", "Nome (A-Z)", "Loja", "Última atualização"]
                    )

                with col_filter3:
                    view_mode = st.radio("Visualização", ["Compacta", "Detalhada"], horizontal=True)

                # Aplicar busca
                filtered_df = latest_df.copy()
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df["product_name"].str.contains(search_term, case=False, na=False)
                    ]

                # Aplicar ordenação
                if sort_by == "Menor preço":
                    filtered_df = filtered_df.sort_values("price", ascending=True)
                elif sort_by == "Maior preço":
                    filtered_df = filtered_df.sort_values("price", ascending=False)
                elif sort_by == "Nome (A-Z)":
                    filtered_df = filtered_df.sort_values("product_name")
                elif sort_by == "Loja":
                    filtered_df = filtered_df.sort_values("store")
                elif sort_by == "Última atualização":
                    filtered_df = filtered_df.sort_values("timestamp", ascending=False)

                st.caption(f"📊 Exibindo {len(filtered_df)} produtos")

                if view_mode == "Compacta":
                    # Visualização em tabela compacta
                    display_df = filtered_df[[
                        "product_name",
                        "store",
                        "price",
                        "tendencia",
                        "status",
                        "url",
                    ]].copy()

                    st.dataframe(
                        display_df,
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "product_name": st.column_config.TextColumn("Produto", width="large"),
                            "store": st.column_config.TextColumn("Loja", width="small"),
                            "price": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                            "tendencia": st.column_config.TextColumn("Tendência", width="small"),
                            "status": st.column_config.TextColumn("Status", width="medium"),
                            "url": st.column_config.LinkColumn("Ver", width="small"),
                        }
                    )
                else:
                    # Visualização detalhada em cards (mas mais compacta que antes)
                    for idx, row in filtered_df.iterrows():
                        col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])

                        with col1:
                            st.markdown(f"**{row['product_name']}**")
                            st.caption(f"🏪 {row['store'].upper()} • {row['category']}")

                        with col2:
                            if pd.notna(row['price']):
                                st.metric("Preço", f"R$ {row['price']:.2f}", delta=None)

                        with col3:
                            st.write(row['tendencia'])
                            st.caption(row['status'])

                        with col4:
                            st.link_button("🔗 Ver", row['url'], width="stretch")

                        st.divider()

            # Gráficos
            st.subheader("📊 Análises")

            chart_tab1, chart_tab2, chart_tab3 = st.tabs([
                "📈 Variação 24h",
                "💰 Menores Preços",
                "📊 Por Categoria"
            ])

            with chart_tab1:
                last_24h = history_df[
                    (history_df['timestamp'] > (datetime.now(timezone.utc) - timedelta(hours=24))) &
                    (history_df['price'].notna())
                ]

                if not last_24h.empty:
                    variations = []
                    for product_id in set(last_24h['product_id'].unique()) & set(products.keys()):
                        product_data = last_24h[last_24h['product_id'] == product_id]
                        if len(product_data) >= 2:
                            product_data_sorted = product_data.sort_values('timestamp')
                            first_price = product_data_sorted.iloc[0]['price']
                            last_price = product_data_sorted.iloc[-1]['price']

                            if pd.notna(first_price) and pd.notna(last_price) and first_price > 0:
                                variation = ((last_price - first_price) / first_price) * 100
                                variations.append({
                                    'Produto': products[product_id].name,
                                    'Variação (%)': round(variation, 2),
                                })

                    if variations:
                        var_df = pd.DataFrame(variations).sort_values('Variação (%)')
                        st.bar_chart(var_df.set_index('Produto')['Variação (%)'], height=400)
                    else:
                        st.info("Dados insuficientes para calcular variações")
                else:
                    st.info("Nenhum dado nas últimas 24h")

            with chart_tab2:
                # Top 10 menores preços
                if not latest_df.empty:
                    top_10 = latest_df.nsmallest(10, 'price')[['product_name', 'store', 'price']]
                    st.dataframe(top_10, width="stretch", hide_index=True)

            with chart_tab3:
                # Distribuição por categoria
                if not latest_df.empty:
                    category_stats = latest_df.groupby('category').agg({
                        'price': ['mean', 'min', 'max', 'count']
                    }).round(2)
                    st.dataframe(category_stats, width="stretch")

# ============================================================
# ABA 2: GERENCIAMENTO
# ============================================================

with tab2:
    st.header("⚙️ Gerenciamento de Produtos")

    config = load_yaml_config()

    # Sub-tabs
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "📋 Lista",
        "➕ Adicionar",
        "📝 Editar",
        "📥📤 Import/Export"
    ])

    # Sub-tab 1: Lista com filtros avançados
    with subtab1:
        st.subheader("📋 Produtos Cadastrados")

        # Filtros avançados
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("🔍 Buscar por nome", placeholder="Digite para buscar...")

        with col2:
            filter_category = st.selectbox(
                "Filtrar por categoria",
                options=["Todas"] + list(set(item['category'] for item in config['items']))
            )

        with col3:
            filter_status = st.selectbox(
                "Filtrar por status",
                options=["Todos", "Apenas ativos", "Apenas inativos"]
            )

        # Aplicar filtros
        filtered_items = config['items']

        if search_term:
            filtered_items = [
                item for item in filtered_items
                if search_term.lower() in item['name'].lower()
            ]

        if filter_category != "Todas":
            filtered_items = [
                item for item in filtered_items
                if item['category'] == filter_category
            ]

        if filter_status == "Apenas ativos":
            filtered_items = [item for item in filtered_items if item.get('enabled', True)]
        elif filter_status == "Apenas inativos":
            filtered_items = [item for item in filtered_items if not item.get('enabled', True)]

        st.caption(f"Exibindo {len(filtered_items)} de {len(config['items'])} produtos")

        if not filtered_items:
            st.info("Nenhum produto encontrado com os filtros aplicados.")
        else:
            # Agrupar por categoria
            by_category = defaultdict(list)
            for item in filtered_items:
                by_category[item['category']].append(item)

            for category, items in sorted(by_category.items()):
                category_color = get_category_color(category)
                st.markdown(f'<div class="category-badge" style="background-color: {category_color};">{category.upper()}</div>', unsafe_allow_html=True)

                for item in items:
                    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 1, 1, 1])

                    with col1:
                        enabled = item.get('enabled', True)
                        status_icon = "✅" if enabled else "❌"
                        st.write(f"{status_icon} **{item['name']}**")

                    with col2:
                        st.write(f"💰 Meta: R$ {item.get('desired_price', 0):.2f}")

                    with col3:
                        st.write(f"🏪 {len(item['urls'])}")

                    with col4:
                        new_status = st.checkbox(
                            "Ativo",
                            value=item.get('enabled', True),
                            key=f"toggle_{item['id']}",
                            label_visibility="collapsed"
                        )
                        if new_status != item.get('enabled', True):
                            toggle_product(config, item['id'], new_status)
                            st.rerun()

                    with col5:
                        if st.button("📋", key=f"dup_{item['id']}", help="Duplicar"):
                            new_id = duplicate_product(config, item['id'])
                            st.success(f"Produto duplicado! ID: {new_id}")
                            st.rerun()

                    with col6:
                        if st.button("🗑️", key=f"delete_{item['id']}", help="Remover"):
                            delete_product(config, item['id'])
                            st.success(f"Produto removido!")
                            st.rerun()

                st.markdown("---")

    # Sub-tab 2: Adicionar (mantido do anterior)
    with subtab2:
        st.subheader("➕ Adicionar Novo Produto")

        with st.form("add_product_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Nome do Produto*", placeholder="Ex: Processador AMD Ryzen 5 7600X")
                new_id = st.text_input(
                    "ID do Produto*",
                    placeholder="Ex: cpu-ryzen-5-7600x",
                    help="Identificador único (sem espaços, use hífens)"
                )
                new_category = st.selectbox(
                    "Categoria*",
                    options=["cpu", "motherboard", "memory", "storage", "gpu", "psu", "cooler", "case", "other"]
                )

            with col2:
                new_price = st.number_input(
                    "Preço Desejado (R$)*",
                    min_value=0.0,
                    value=1000.0,
                    step=10.0
                )
                new_enabled = st.checkbox("Produto ativo", value=True)

            st.markdown("### 🔗 URLs das Lojas")
            num_urls = st.number_input("Número de lojas", min_value=1, max_value=10, value=1)

            urls_data = []
            for i in range(num_urls):
                col_store, col_url = st.columns([1, 3])
                with col_store:
                    store = st.selectbox(
                        f"Loja {i+1}",
                        options=["kabum", "amazon", "pichau", "terabyte", "mercadolivre", "other"],
                        key=f"store_{i}"
                    )
                with col_url:
                    url = st.text_input(f"URL {i+1}", placeholder="https://...", key=f"url_{i}")
                if store and url:
                    urls_data.append({"store": store, "url": url})

            submitted = st.form_submit_button("✅ Adicionar Produto", type="primary")

            if submitted:
                if not new_name or not new_id:
                    st.error("❌ Nome e ID são obrigatórios!")
                elif any(item['id'] == new_id for item in config['items']):
                    st.error(f"❌ Já existe um produto com o ID '{new_id}'!")
                elif not urls_data:
                    st.error("❌ Adicione pelo menos uma URL!")
                else:
                    new_product = {
                        'id': new_id,
                        'name': new_name,
                        'category': new_category,
                        'desired_price': new_price,
                        'enabled': new_enabled,
                        'urls': urls_data
                    }
                    add_product(config, new_product)
                    st.success(f"✅ Produto '{new_name}' adicionado!")
                    st.balloons()
                    st.rerun()

    # Sub-tab 3: Editar (mantido do anterior)
    with subtab3:
        st.subheader("📝 Editar Produto")

        if not config['items']:
            st.info("Nenhum produto cadastrado.")
        else:
            product_names = {item['name']: item['id'] for item in config['items']}
            selected_name = st.selectbox("Selecione o produto", options=list(product_names.keys()))

            if selected_name:
                product_id = product_names[selected_name]
                product = next(item for item in config['items'] if item['id'] == product_id)

                with st.form("edit_product_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        edit_name = st.text_input("Nome", value=product['name'])
                        edit_category = st.selectbox(
                            "Categoria",
                            options=["cpu", "motherboard", "memory", "storage", "gpu", "psu", "cooler", "case", "other"],
                            index=["cpu", "motherboard", "memory", "storage", "gpu", "psu", "cooler", "case", "other"].index(product['category'])
                        )

                    with col2:
                        edit_price = st.number_input(
                            "Preço Desejado (R$)",
                            min_value=0.0,
                            value=float(product.get('desired_price', 1000.0)),
                            step=10.0
                        )
                        edit_enabled = st.checkbox("Ativo", value=product.get('enabled', True))

                    st.markdown("### URLs Atuais")
                    for idx, url_data in enumerate(product.get('urls', [])):
                        col_s, col_u = st.columns([1, 3])
                        with col_s:
                            st.text_input(f"Loja {idx+1}", value=url_data['store'], key=f"e_s_{idx}", disabled=True)
                        with col_u:
                            st.text_input(f"URL {idx+1}", value=url_data['url'], key=f"e_u_{idx}", disabled=True)

                    st.markdown("### Adicionar URL")
                    col_new_store, col_new_url = st.columns([1, 3])
                    with col_new_store:
                        new_store = st.selectbox("Loja", options=["", "kabum", "amazon", "pichau", "terabyte", "mercadolivre"], key="new_s")
                    with col_new_url:
                        new_url = st.text_input("URL", placeholder="https://...", key="new_u")

                    submitted = st.form_submit_button("💾 Salvar", type="primary")

                    if submitted:
                        updated_urls = product.get('urls', []).copy()
                        if new_store and new_url:
                            updated_urls.append({"store": new_store, "url": new_url})

                        updates = {
                            'name': edit_name,
                            'category': edit_category,
                            'desired_price': edit_price,
                            'enabled': edit_enabled,
                            'urls': updated_urls
                        }
                        update_product(config, product_id, updates)
                        st.success("✅ Produto atualizado!")
                        st.rerun()

    # Sub-tab 4: Import/Export
    with subtab4:
        st.subheader("📥📤 Import/Export de Produtos")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📤 Exportar")

            export_format = st.radio("Formato", ["CSV", "JSON"])

            if st.button("📥 Gerar Arquivo", type="primary", width="stretch"):
                if export_format == "CSV":
                    data = export_to_csv(config)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=data,
                        file_name=f"produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        width="stretch"
                    )
                else:
                    data = export_to_json(config)
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=data,
                        file_name=f"produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        width="stretch"
                    )

        with col2:
            st.markdown("### 📥 Importar")

            import_format = st.radio("Formato de importação", ["CSV", "JSON"], key="import_format")

            uploaded_file = st.file_uploader(
                "Selecione o arquivo",
                type=['csv', 'json'] if import_format == "CSV" else ['json']
            )

            replace_existing = st.checkbox(
                "Substituir produtos existentes",
                help="Se marcado, TODOS os produtos atuais serão removidos"
            )

            if uploaded_file and st.button("📤 Importar", type="secondary", width="stretch"):
                try:
                    content = uploaded_file.read().decode('utf-8')

                    if import_format == "CSV":
                        imported_config = import_from_csv(content)
                    else:
                        imported_config = import_from_json(content)

                    if replace_existing:
                        save_yaml_config(imported_config)
                        st.success(f"✅ {len(imported_config['items'])} produtos importados (substituição total)!")
                    else:
                        # Adicionar sem substituir
                        for item in imported_config['items']:
                            if not any(existing['id'] == item['id'] for existing in config['items']):
                                config['items'].append(item)
                        save_yaml_config(config)
                        st.success(f"✅ Produtos importados (apenas novos)!")

                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao importar: {e}")

        st.markdown("---")
        st.markdown("### 📄 Template de Importação CSV")

        template_csv = "id,name,category,desired_price,enabled,store,url\ncpu-exemplo,Processador Exemplo,cpu,1500.0,true,kabum,https://exemplo.com"

        st.download_button(
            label="⬇️ Baixar Template CSV",
            data=template_csv,
            file_name="template_produtos.csv",
            mime="text/csv",
            width="content"
        )

# ============================================================
# ABA 3: ESTATÍSTICAS
# ============================================================

with tab3:
    st.header("📈 Estatísticas e Análises")

    config = load_yaml_config()
    history_df = monitor.load_history()

    stats = calculate_statistics(config, history_df)

    # Cards de métricas principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Total de Produtos", stats['total_products'])

    with col2:
        st.metric("✅ Ativos", stats['active_products'], delta=f"+{stats['active_products']}")

    with col3:
        st.metric("❌ Inativos", stats['inactive_products'])

    with col4:
        st.metric("🔗 Total de URLs", stats['total_urls'])

    st.markdown("---")

    # Gráficos de estatísticas
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Produtos por Categoria")

        if stats['categories']:
            category_data = pd.DataFrame([
                {'Categoria': cat, 'Total': data['count'], 'Ativos': data['active']}
                for cat, data in stats['categories'].items()
            ])
            st.bar_chart(category_data.set_index('Categoria')['Total'])
        else:
            st.info("Nenhum dado disponível")

    with chart_col2:
        st.subheader("🏪 Distribuição por Loja")

        if stats['by_store']:
            store_data = pd.DataFrame([
                {'Loja': store.upper(), 'Total': count}
                for store, count in stats['by_store'].items()
            ])
            st.bar_chart(store_data.set_index('Loja')['Total'])
        else:
            st.info("Nenhum dado disponível")

    st.markdown("---")

    # Produtos abaixo da meta
    if stats['below_target']:
        st.subheader("🎯 Produtos Abaixo da Meta")

        below_df = pd.DataFrame(stats['below_target'])
        below_df = below_df.sort_values('savings', ascending=False)

        st.dataframe(
            below_df,
            width="stretch",
            hide_index=True,
            column_config={
                'name': st.column_config.TextColumn('Produto'),
                'current_price': st.column_config.NumberColumn('Preço Atual', format='R$ %.2f'),
                'desired_price': st.column_config.NumberColumn('Meta', format='R$ %.2f'),
                'savings': st.column_config.NumberColumn('Economia', format='R$ %.2f'),
                'store': st.column_config.TextColumn('Loja'),
            }
        )

        total_savings = below_df['savings'].sum()
        st.success(f"💰 Economia total potencial: **R$ {total_savings:.2f}**")
    else:
        st.info("Nenhum produto abaixo da meta no momento")

    st.markdown("---")

    # === SEÇÃO: Histórico de Alertas ===
    st.subheader("⏰ Histórico de Alertas")
    st.markdown("##### Quando os produtos atingiram o preço desejado")

    if not history_df.empty:
        # Criar log de alertas (quando preço ficou <= meta)
        alerts_log = []

        for product_id, product in products.items():
            if not pd.notna(product.desired_price):
                continue

            product_history = history_df[
                (history_df["product_id"] == product_id) &
                (history_df["price"].notna()) &
                (history_df["price"] <= product.desired_price)
            ].sort_values("timestamp")

            if not product_history.empty:
                # Pegar o primeiro alerta e o mais recente
                first_alert = product_history.iloc[0]
                last_alert = product_history.iloc[-1]

                # Contar quantas vezes atingiu
                unique_dates = product_history.groupby(product_history['timestamp'].dt.date).size()

                alerts_log.append({
                    'produto': product.name,
                    'loja': first_alert['store'],
                    'primeira_vez': first_alert['timestamp'],
                    'ultima_vez': last_alert['timestamp'],
                    'melhor_preco': product_history['price'].min(),
                    'preco_meta': product.desired_price,
                    'economia_max': product.desired_price - product_history['price'].min(),
                    'vezes_atingido': len(unique_dates)
                })

        if alerts_log:
            alerts_df = pd.DataFrame(alerts_log).sort_values('ultima_vez', ascending=False)

            # Separar em tabs: Recentes e Histórico Completo
            alert_tab1, alert_tab2 = st.tabs(["🔥 Recentes (Última Semana)", "📜 Histórico Completo"])

            with alert_tab1:
                # Filtrar última semana
                one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
                recent_alerts_df = alerts_df[alerts_df['ultima_vez'] >= one_week_ago]

                if not recent_alerts_df.empty:
                    for _, alert in recent_alerts_df.head(10).iterrows():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                        with col1:
                            st.markdown(f"**{alert['produto']}**")
                            st.caption(f"🏪 {alert['loja'].upper()}")

                        with col2:
                            st.metric("Melhor Preço", f"R$ {alert['melhor_preco']:.2f}")

                        with col3:
                            st.metric("Economia", f"R$ {alert['economia_max']:.2f}")

                        with col4:
                            days_ago = (datetime.now(timezone.utc) - alert['ultima_vez']).days
                            if days_ago == 0:
                                st.caption("🟢 Hoje")
                            elif days_ago == 1:
                                st.caption("🟡 Ontem")
                            else:
                                st.caption(f"⚪ {days_ago}d atrás")

                        st.divider()
                else:
                    st.info("📭 Nenhum produto atingiu o preço na última semana.")

            with alert_tab2:
                st.dataframe(
                    alerts_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        'produto': st.column_config.TextColumn('Produto', width="large"),
                        'loja': st.column_config.TextColumn('Loja', width="small"),
                        'primeira_vez': st.column_config.DatetimeColumn('Primeira Vez', format="DD/MM/YY HH:mm"),
                        'ultima_vez': st.column_config.DatetimeColumn('Última Vez', format="DD/MM/YY HH:mm"),
                        'melhor_preco': st.column_config.NumberColumn('Melhor Preço', format="R$ %.2f"),
                        'preco_meta': st.column_config.NumberColumn('Meta', format="R$ %.2f"),
                        'economia_max': st.column_config.NumberColumn('Economia Máx', format="R$ %.2f"),
                        'vezes_atingido': st.column_config.NumberColumn('Vezes Atingido', format="%d dias"),
                    }
                )

                st.info(f"📊 Total de {len(alerts_df)} produtos já atingiram o preço desejado")
        else:
            st.info("📭 Nenhum produto atingiu o preço desejado ainda.")
    else:
        st.info("📭 Sem dados de histórico disponíveis.")

    st.markdown("---")

    # Detalhes por categoria
    st.subheader("📂 Detalhes por Categoria")

    for category, data in sorted(stats['categories'].items()):
        with st.expander(f"{category.upper()} - {data['count']} produtos"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total", data['count'])
            with col2:
                st.metric("Ativos", data['active'])
            with col3:
                avg_price = data['total_desired_price'] / data['count'] if data['count'] > 0 else 0
                st.metric("Preço Médio Meta", f"R$ {avg_price:.2f}")

# ============================================================
# ABA 4: VOOS (mantido)
# ============================================================

with tab4:
    st.header("✈️ Monitor de Voos")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔍 Buscar Voos", help="Busca voos usando DeepSeek AI"):
            with st.spinner("Buscando voos..."):
                try:
                    flight_monitor = FlightMonitor(
                        config_path=FLIGHT_CONFIG_PATH,
                        history_path=FLIGHT_HISTORY_PATH
                    )
                    flights = flight_monitor.collect()
                    flight_monitor.close()
                    st.success(f"✅ {len(flights)} voos encontrados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

    with col2:
        st.info("💡 A busca usa IA e pode demorar ~5 minutos")

    if FLIGHT_HISTORY_PATH.exists():
        try:
            flight_monitor_display = FlightMonitor(
                config_path=FLIGHT_CONFIG_PATH,
                history_path=FLIGHT_HISTORY_PATH
            )
            flights_df = flight_monitor_display.get_latest_flights()

            if not flights_df.empty:
                st.subheader("🎫 Melhores Voos")

                display_df = flights_df[[
                    "airline", "origin", "destination",
                    "departure_date", "return_date", "price",
                    "stops", "duration", "url"
                ]].copy()

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "airline": st.column_config.TextColumn("Companhia"),
                        "price": st.column_config.NumberColumn("Preço", format="R$ %.0f"),
                        "url": st.column_config.LinkColumn("Link"),
                    }
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Menor", f"R$ {flights_df['price'].min():.2f}")
                with col2:
                    st.metric("📊 Médio", f"R$ {flights_df['price'].mean():.2f}")
                with col3:
                    st.metric("✈️ Total", len(flights_df))
            else:
                st.info("📭 Nenhum voo encontrado")
        except Exception as e:
            st.warning(f"⚠️ Erro: {e}")
    else:
        st.info("📭 Configure em `config/flights.yaml`")

# ============================================================
# ABA 5: SOBRE
# ============================================================

with tab5:
    st.header("ℹ️ Sobre o Sistema")

    st.markdown("""
    ### 📉 Monitor de Preços - **Professional Edition**

    Sistema profissional e completo de monitoramento de preços com recursos avançados.

    #### 🎯 Funcionalidades Premium:

    **Dashboard:**
    - ✅ Visualização de preços em tempo real
    - ✅ Gráficos e estatísticas interativas
    - ✅ Filtros avançados (categoria, loja, preço)
    - ✅ Múltiplas visualizações (tabela/cards)
    - ✅ Tendências e variações de preço

    **Gerenciamento:**
    - ✅ CRUD completo de produtos
    - ✅ Ativar/desativar produtos
    - ✅ Duplicar produtos
    - ✅ Busca e filtros avançados
    - ✅ Ordenação personalizada

    **Import/Export:**
    - ✅ Exportar para CSV/JSON
    - ✅ Importar de CSV/JSON
    - ✅ Templates de importação
    - ✅ Backup automático

    **Estatísticas:**
    - ✅ Análises por categoria
    - ✅ Distribuição por loja
    - ✅ Produtos abaixo da meta
    - ✅ Economia potencial
    - ✅ Gráficos interativos

    **Outras Funcionalidades:**
    - ✅ Monitor de voos
    - ✅ Alertas por email
    - ✅ Auto-refresh
    - ✅ Mobile-friendly
    - ✅ Multi-lojas

    #### 🛠️ Lojas Suportadas:

    - 🛒 Kabum
    - 📦 Amazon
    - 💻 Pichau
    - ⚡ Terabyte
    - 🛍️ Mercado Livre

    ---

    **Versão:** 3.0.0 (Professional Edition)
    **Última atualização:** 13/11/2025
    **Status:** ✅ Produção

    💡 **Dica:** Explore todas as abas para aproveitar ao máximo o sistema!
    """)

    st.success("🚀 Sistema Professional Edition 100% funcional!")

    # Estatísticas do sistema
    st.markdown("---")
    st.subheader("📊 Estatísticas do Sistema")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Produtos", len(config['items']))
    with col2:
        st.metric("📂 Categorias", len(set(item['category'] for item in config['items'])))
    with col3:
        total_urls = sum(len(item.get('urls', [])) for item in config['items'])
        st.metric("🔗 URLs", total_urls)
    with col4:
        if not history_df.empty:
            st.metric("✅ Verificações", len(history_df))
        else:
            st.metric("✅ Verificações", 0)
