"""Settings page - configurações de alertas, scraping e sistema."""

import streamlit as st
from pathlib import Path
import yaml


def render():
    """Render settings page."""

    st.header("🔧 Configurações do Sistema")

    config_path = Path("config/config.yaml")
    if not config_path.exists():
        st.error("Arquivo config.yaml não encontrado!")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Sub-tabs
    tab1, tab2, tab3 = st.tabs([
        "📧 Alertas",
        "🕷️ Scraping",
        "⚙️ Sistema"
    ])

    with tab1:
        render_alerts_settings(config)

    with tab2:
        render_scraping_settings(config)

    with tab3:
        render_system_settings(config)


def render_alerts_settings(config):
    """Alert settings."""
    st.subheader("Configurações de Alertas")

    alerts_config = config.get("alerts", {})

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Status de Alertas", "✅ Ativo" if alerts_config.get("enabled", True) else "❌ Desativado")
        st.metric("Cooldown", f"{alerts_config.get('cooldown_hours', 6)} horas")
        st.metric("Email Destinatário", alerts_config.get("recipient", "Não configurado"))

    with col2:
        triggers = alerts_config.get("triggers", {})
        st.metric("Queda de Preço (threshold)", f"{triggers.get('price_drop_percent', 5)}%")
        st.metric("Produtos Prioritários (threshold)", f"{triggers.get('priority_price_drop_percent', 2)}%")
        st.metric("Alertar abaixo do desejado", "✅ Sim" if triggers.get("below_desired_price", True) else "❌ Não")

    st.divider()

    st.markdown("### Produtos Prioritários")
    priority_products = alerts_config.get("priority_products", [])
    if priority_products:
        for prod in priority_products:
            st.caption(f"⭐ {prod}")
    else:
        st.info("Nenhum produto prioritário configurado.")

    st.divider()
    st.info("💡 **Edite `config/config.yaml` para modificar alertas.**")
    st.info("🔐 **Credenciais de email:** Configure em `config/.secrets.yaml`")


def render_scraping_settings(config):
    """Scraping settings."""
    st.subheader("Configurações de Scraping")

    scraping_config = config.get("scraping", {})
    selenium_config = scraping_config.get("selenium", {})

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Selenium:**")
        st.metric("Modo Headless", "✅ Sim" if selenium_config.get("headless", True) else "❌ Não")
        st.metric("Timeout", f"{selenium_config.get('timeout', 30)}s")
        st.metric("Máximo de Retries", selenium_config.get("max_retries", 5))

    with col2:
        st.write("**Rate Limiting:**")
        st.metric("Delay entre requests", f"{scraping_config.get('delay_seconds', 2)}s")
        st.metric("Requests por loja", scraping_config.get("rate_limit_per_store", 5))

    st.divider()

    st.markdown("### Validação de Preços")
    price_validation = scraping_config.get("price_validation", {})

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Preço Mínimo Global", f"R$ {price_validation.get('min_price', 50):.2f}")
        st.metric("Preço Máximo Global", f"R$ {price_validation.get('max_price', 50000):.2f}")

    with col2:
        st.metric("Aumento Máximo Permitido", f"{price_validation.get('max_increase_percent', 150)}%")
        st.metric("Queda Máxima Permitida", f"{price_validation.get('max_decrease_percent', 90)}%")

    st.divider()

    st.markdown("### Limites por Categoria")
    category_limits = price_validation.get("category_limits", {})

    if category_limits:
        for cat_name, limits in category_limits.items():
            st.caption(f"**{cat_name.upper()}:** R$ {limits.get('min', 0):.2f} - R$ {limits.get('max', 0):.2f}")

    st.divider()
    st.info("💡 **Edite `config/config.yaml` para modificar configurações de scraping.**")


def render_system_settings(config):
    """System settings."""
    st.subheader("Configurações do Sistema")

    general_config = config.get("general", {})
    performance_config = config.get("performance", {})
    logging_config = config.get("logging", {})

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Geral:**")
        st.metric("Intervalo de Verificação", f"{general_config.get('check_interval_minutes', 60)} min")
        st.metric("Timezone", general_config.get("timezone", "America/Sao_Paulo"))

        st.divider()

        st.write("**Performance:**")
        st.metric("Cache Ativo", "✅ Sim" if performance_config.get("use_cache", True) else "❌ Não")
        st.metric("TTL do Cache", f"{performance_config.get('cache_ttl_minutes', 30)} min")

    with col2:
        st.write("**Logging:**")
        st.metric("Nível de Log", logging_config.get("level", "INFO"))
        st.metric("Arquivo de Log", logging_config.get("file", "logs/monitor.log"))

    st.divider()

    # System info
    st.markdown("### Informações do Sistema")

    st.write("**Arquivos de Dados:**")
    data_files = {
        "Histórico de Preços": "data/price_history.csv",
        "Histórico de Alertas": "data/alert_history.csv",
        "Histórico de Voos": "data/flight_history.csv",
        "Histórico de Open Box": "data/openbox_history.csv",
    }

    for name, path in data_files.items():
        file_path = Path(path)
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            st.caption(f"✅ {name}: {size_kb:.1f} KB ({path})")
        else:
            st.caption(f"❌ {name}: Não encontrado ({path})")

    st.divider()
    st.info("💡 **Edite `config/config.yaml` para modificar configurações do sistema.**")
