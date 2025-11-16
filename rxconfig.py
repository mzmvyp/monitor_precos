"""Configuração do Reflex para Monitor de Preços Professional."""

import reflex as rx

config = rx.Config(
    app_name="monitor_app",
    # Performance
    backend_port=8000,
    frontend_port=3000,
    # Deploy
    deploy_url="http://localhost:3000",
    # Database (opcional - para futuro)
    db_url="sqlite:///reflex.db",
    # Tema
    tailwind={
        "theme": {
            "extend": {
                "colors": {
                    "primary": {
                        "50": "#f0f9ff",
                        "100": "#e0f2fe",
                        "500": "#0ea5e9",
                        "600": "#0284c7",
                        "700": "#0369a1",
                    },
                    "success": {
                        "500": "#10b981",
                        "600": "#059669",
                    },
                    "warning": {
                        "500": "#f59e0b",
                        "600": "#d97706",
                    },
                    "danger": {
                        "500": "#ef4444",
                        "600": "#dc2626",
                    },
                }
            }
        }
    },
)
