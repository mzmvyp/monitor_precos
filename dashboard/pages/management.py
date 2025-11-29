"""Management page - CRUD para produtos, voos e open box."""

import streamlit as st
from pathlib import Path
import yaml


def render():
    """Render management page."""

    st.header("⚙️ Gerenciamento de Itens")

    st.info("💡 **Dica:** As configurações são salvas em `config/config.yaml`. Edite o arquivo diretamente para maior controle.")

    # Sub-tabs
    tab1, tab2, tab3 = st.tabs([
        "🛒 Produtos",
        "✈️ Voos",
        "📦 Open Box"
    ])

    with tab1:
        render_products_management()

    with tab2:
        render_flights_management()

    with tab3:
        render_openbox_management()


def render_products_management():
    """Manage products."""
    st.subheader("Gerenciar Produtos")

    config_path = Path("config/config.yaml")
    if not config_path.exists():
        st.error("Arquivo config.yaml não encontrado!")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    products = config.get("products", [])

    if not products:
        st.warning("Nenhum produto configurado.")
        return

    # Listar produtos
    st.markdown("### Produtos Configurados")

    for i, product in enumerate(products):
        with st.expander(f"📦 {product.get('name', 'Sem nome')} ({product.get('id', 'no-id')})"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Categoria:** {product.get('category', 'N/A')}")
                st.write(f"**Preço Desejado:** R$ {product.get('desired_price', 0):.2f}")
                st.write(f"**Status:** {'✅ Ativo' if product.get('enabled', True) else '❌ Desativado'}")
                st.write(f"**URLs monitoradas:** {len(product.get('urls', []))}")

                # Mostrar URLs
                for url_data in product.get('urls', []):
                    st.caption(f"- {url_data.get('store', 'unknown')}: {url_data.get('url', '')[:80]}...")

            with col2:
                st.write("**Ações:**")
                if st.button("🗑️ Remover", key=f"del_prod_{i}"):
                    st.warning("Funcionalidade em desenvolvimento")

    st.divider()
    st.markdown("### Adicionar Novo Produto")
    st.info("🚧 Edite `config/config.yaml` diretamente para adicionar produtos.")


def render_flights_management():
    """Manage flights."""
    st.subheader("Gerenciar Voos")

    config_path = Path("config/config.yaml")
    if not config_path.exists():
        st.error("Arquivo config.yaml não encontrado!")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    flights = config.get("flights", [])

    if not flights:
        st.warning("Nenhum voo configurado.")
        return

    # Listar voos
    for i, flight in enumerate(flights):
        with st.expander(f"✈️ {flight.get('name', 'Sem nome')}"):
            st.write(f"**Origem:** {flight.get('origin')}")
            st.write(f"**Destinos:** {', '.join(flight.get('destinations', []))}")
            st.write(f"**Datas de ida:** {len(flight.get('departure_dates', []))} opções")
            st.write(f"**Preço máximo:** R$ {flight.get('max_price', 0):.2f}")
            st.write(f"**Preço de alerta:** R$ {flight.get('alert_price', 0):.2f}")

    st.divider()
    st.info("🚧 Edite `config/config.yaml` para gerenciar voos.")


def render_openbox_management():
    """Manage open box categories."""
    st.subheader("Gerenciar Categorias Open Box")

    config_path = Path("config/config.yaml")
    if not config_path.exists():
        st.error("Arquivo config.yaml não encontrado!")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    openbox_config = config.get("open_box", {})
    categories = openbox_config.get("categories", {})

    if not categories:
        st.warning("Nenhuma categoria Open Box configurada.")
        return

    # Listar categorias
    for cat_name, cat_config in categories.items():
        with st.expander(f"📦 {cat_name.upper()}"):
            st.write(f"**Status:** {'✅ Ativo' if cat_config.get('enabled', False) else '❌ Desativado'}")
            st.write(f"**URL:** {cat_config.get('url', '')[:80]}...")

            filters = cat_config.get('filters', {})
            st.write("**Filtros:**")
            for key, value in filters.items():
                st.caption(f"- {key}: {value}")

    st.divider()
    st.info("🚧 Edite `config/config.yaml` para configurar Open Box.")
