from __future__ import annotations

import logging
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

st.set_page_config(page_title="Monitor de Preços - Black Friday", layout="wide", initial_sidebar_state="expanded")

# Funções auxiliares para gerenciamento de produtos
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

# Título principal
st.title("📉 Monitor de Preços - Black Friday")

# Criar abas principais
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "⚙️ Gerenciamento", "✈️ Voos", "ℹ️ Sobre"])

# ============================================================
# ABA 1: DASHBOARD (código existente)
# ============================================================
with tab1:
    st.session_state.setdefault("auto_refresh_enabled", True)
    st.session_state.setdefault("auto_refresh_interval", 5)

    monitor = PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)
    products = monitor.products

    # Filtrar apenas produtos ativos
    yaml_config = load_yaml_config()
    active_products = {
        prod_id: prod for prod_id, prod in products.items()
        if any(item['id'] == prod_id and item.get('enabled', True) for item in yaml_config['items'])
    }

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
        try:
            with st.spinner("Coletando preços atualizados... Isso pode levar alguns minutos."):
                snapshots = monitor.collect(product_ids=selected_ids)

            if snapshots:
                st.success(f"✅ Coleta finalizada: {len(snapshots)} registros coletados!")
            else:
                st.warning("⚠️ Nenhum preço foi coletado. Verifique os logs.")

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
                streamlit run streamlit_app.py
                ```

                **Passo 5:** Tente atualizar preços novamente

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

    with st.sidebar:
        st.header("Configurações")
        product_options = {prod.name: prod.id for prod in active_products.values()}
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
    else:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], utc=True)

        if selected_category != "Todas":
            history_df = history_df[history_df["category"] == selected_category]

        # Filtrar apenas produtos ativos
        active_product_ids = set(active_products.keys())
        history_df = history_df[history_df["product_id"].isin(active_product_ids)]

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
# ABA 2: GERENCIAMENTO DE PRODUTOS
# ============================================================
with tab2:
    st.header("⚙️ Gerenciamento de Produtos")

    config = load_yaml_config()

    # Sub-tabs para organizar melhor
    subtab1, subtab2, subtab3 = st.tabs(["📋 Lista de Produtos", "➕ Adicionar Produto", "📝 Editar Produto"])

    # Sub-tab 1: Lista de produtos com ativar/desativar
    with subtab1:
        st.subheader("📋 Produtos Cadastrados")

        if not config['items']:
            st.info("Nenhum produto cadastrado ainda. Adicione um produto na aba 'Adicionar Produto'.")
        else:
            # Agrupar por categoria
            from collections import defaultdict
            by_category = defaultdict(list)
            for item in config['items']:
                by_category[item['category']].append(item)

            for category, items in sorted(by_category.items()):
                st.markdown(f"### {category.upper()}")

                for item in items:
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

                    with col1:
                        enabled = item.get('enabled', True)
                        status_icon = "✅" if enabled else "❌"
                        st.write(f"{status_icon} **{item['name']}**")

                    with col2:
                        st.write(f"💰 Meta: R$ {item.get('desired_price', 0):.2f}")

                    with col3:
                        st.write(f"🏪 {len(item['urls'])} lojas")

                    with col4:
                        # Toggle ativar/desativar
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
                        # Botão para deletar
                        if st.button("🗑️", key=f"delete_{item['id']}", help="Remover produto"):
                            delete_product(config, item['id'])
                            st.success(f"Produto '{item['name']}' removido!")
                            st.rerun()

                st.markdown("---")

    # Sub-tab 2: Adicionar novo produto
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
            st.caption("Adicione pelo menos uma URL")

            # Adicionar múltiplas URLs
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
                    url = st.text_input(
                        f"URL {i+1}",
                        placeholder="https://...",
                        key=f"url_{i}"
                    )
                if store and url:
                    urls_data.append({"store": store, "url": url})

            submitted = st.form_submit_button("✅ Adicionar Produto", type="primary")

            if submitted:
                # Validações
                if not new_name or not new_id:
                    st.error("❌ Nome e ID são obrigatórios!")
                elif any(item['id'] == new_id for item in config['items']):
                    st.error(f"❌ Já existe um produto com o ID '{new_id}'!")
                elif not urls_data:
                    st.error("❌ Adicione pelo menos uma URL!")
                else:
                    # Criar novo produto
                    new_product = {
                        'id': new_id,
                        'name': new_name,
                        'category': new_category,
                        'desired_price': new_price,
                        'enabled': new_enabled,
                        'urls': urls_data
                    }

                    add_product(config, new_product)
                    st.success(f"✅ Produto '{new_name}' adicionado com sucesso!")
                    st.balloons()
                    st.rerun()

    # Sub-tab 3: Editar produto existente
    with subtab3:
        st.subheader("📝 Editar Produto Existente")

        if not config['items']:
            st.info("Nenhum produto cadastrado para editar.")
        else:
            # Selecionar produto para editar
            product_names = {item['name']: item['id'] for item in config['items']}
            selected_name = st.selectbox("Selecione o produto para editar", options=list(product_names.keys()))

            if selected_name:
                product_id = product_names[selected_name]
                product = next(item for item in config['items'] if item['id'] == product_id)

                with st.form("edit_product_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        edit_name = st.text_input("Nome do Produto", value=product['name'])
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
                        edit_enabled = st.checkbox("Produto ativo", value=product.get('enabled', True))

                    st.markdown("### 🔗 URLs das Lojas")

                    # Mostrar URLs existentes
                    existing_urls = product.get('urls', [])
                    st.caption(f"URLs atuais: {len(existing_urls)}")

                    for idx, url_data in enumerate(existing_urls):
                        col_store, col_url, col_remove = st.columns([1, 3, 0.5])
                        with col_store:
                            st.text_input(f"Loja {idx+1}", value=url_data['store'], key=f"edit_store_{idx}", disabled=True)
                        with col_url:
                            st.text_input(f"URL {idx+1}", value=url_data['url'], key=f"edit_url_{idx}", disabled=True)
                        with col_remove:
                            st.write("") # Espaço

                    # Adicionar nova URL
                    st.markdown("#### ➕ Adicionar Nova URL")
                    col_new_store, col_new_url = st.columns([1, 3])
                    with col_new_store:
                        new_store = st.selectbox(
                            "Loja",
                            options=["", "kabum", "amazon", "pichau", "terabyte", "mercadolivre", "other"],
                            key="new_store_edit"
                        )
                    with col_new_url:
                        new_url = st.text_input("URL", placeholder="https://...", key="new_url_edit")

                    submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")

                    if submitted:
                        # Preparar URLs atualizadas
                        updated_urls = existing_urls.copy()
                        if new_store and new_url:
                            updated_urls.append({"store": new_store, "url": new_url})

                        # Atualizar produto
                        updates = {
                            'name': edit_name,
                            'category': edit_category,
                            'desired_price': edit_price,
                            'enabled': edit_enabled,
                            'urls': updated_urls
                        }

                        update_product(config, product_id, updates)
                        st.success(f"✅ Produto '{edit_name}' atualizado com sucesso!")
                        st.rerun()

# ============================================================
# ABA 3: VOOS
# ============================================================
with tab3:
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

# ============================================================
# ABA 4: SOBRE
# ============================================================
with tab4:
    st.header("ℹ️ Sobre o Sistema")

    st.markdown("""
    ### 📉 Monitor de Preços - Black Friday

    Sistema profissional de monitoramento de preços desenvolvido para rastrear os melhores
    preços em diversas lojas online.

    #### 🎯 Funcionalidades:

    - **Dashboard Completo**: Visualize preços, tendências e histórico
    - **Gerenciamento de Produtos**: Adicione, edite e ative/desative produtos
    - **Alertas por Email**: Receba notificações quando preços caírem
    - **Multi-lojas**: Kabum, Amazon, Pichau, Terabyte e mais
    - **Mobile-friendly**: Interface otimizada para celular
    - **Gráficos e Estatísticas**: Acompanhe variações de preço

    #### 🛠️ Lojas Suportadas:

    - 🛒 Kabum
    - 📦 Amazon
    - 💻 Pichau
    - ⚡ Terabyte
    - 🛍️ Mercado Livre

    #### 📝 Como Usar:

    1. **Adicione produtos** na aba "Gerenciamento"
    2. **Configure o preço desejado** para cada produto
    3. **Ative o monitoramento** dos produtos que deseja acompanhar
    4. **Visualize no Dashboard** os melhores preços
    5. **Receba alertas** quando os preços atingirem sua meta

    #### ⚙️ Configurações Avançadas:

    - Configure alertas de email em `config/alerts.yaml`
    - Ajuste intervalo de scraping
    - Personalize categorias de produtos

    ---

    **Versão:** 2.0.0 (Professional Edition)
    **Última atualização:** 13/11/2025
    **Correções aplicadas:** ✅ Bugs críticos corrigidos

    💡 **Dica:** Use a aba "Gerenciamento" para adicionar novos produtos e organizar seu monitoramento!
    """)

    st.success("🚀 Sistema 100% funcional e pronto para uso!")
