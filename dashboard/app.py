"""
Dashboard Principal - Monitor de Preços
Interface modular e unificada com 3 abas principais.
"""

import streamlit as st
from pathlib import Path
import sys

# Adicionar diretório raiz ao path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from dashboard.pages import dashboard, management, settings


def main():
    """Entry point do dashboard."""

    st.set_page_config(
        page_title="Monitor de Preços - Professional Edition",
        layout="wide",
        page_icon="📉",
        initial_sidebar_state="collapsed"
    )

    # Header
    st.markdown("""
    <h1 style='text-align: center;'>
        📉 Monitor de Preços - Professional Edition
    </h1>
    <p style='text-align: center; color: gray;'>
        Sistema avançado de monitoramento e gestão de preços
    </p>
    <hr>
    """, unsafe_allow_html=True)

    # Tabs principais (3 abas conforme plano)
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard",      # Produtos + Open Box + Voos
        "⚙️ Gerenciamento", # CRUD de produtos/voos/open box
        "🔧 Configurações"  # Alertas + Scraping + Sistema
    ])

    with tab1:
        dashboard.render()

    with tab2:
        management.render()

    with tab3:
        settings.render()


if __name__ == "__main__":
    main()
