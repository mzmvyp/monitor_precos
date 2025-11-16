"""Componentes de Alertas e Notificações."""

import reflex as rx
from ..styles import ALERT_STYLE, COLORS


def alert_banner(
    message: str,
    alert_type: str = "info",  # success, warning, danger, info
    icon: str = "",
    dismissible: bool = False,
) -> rx.Component:
    """Banner de alerta profissional."""

    icon_map = {
        "success": "✅",
        "warning": "⚠️",
        "danger": "❌",
        "info": "ℹ️",
    }

    display_icon = icon or icon_map.get(alert_type, "ℹ️")
    style = ALERT_STYLE.get(alert_type, ALERT_STYLE["info"])

    return rx.box(
        rx.hstack(
            rx.text(display_icon, font_size="1.5rem"),
            rx.box(
                rx.markdown(message),
                flex="1",
            ),
            rx.cond(
                dismissible,
                rx.button(
                    "×",
                    bg="transparent",
                    color="inherit",
                    font_size="1.5rem",
                    padding="0",
                    _hover={"opacity": 0.7},
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        **style,
        class_name="fade-in",
    )


def notification_toast(
    message: str,
    toast_type: str = "success",
) -> rx.Component:
    """Toast notification (para mensagens temporárias)."""

    color_map = {
        "success": COLORS["success"],
        "error": COLORS["danger"],
        "warning": COLORS["warning"],
        "info": COLORS["info"],
    }

    bg_color = color_map.get(toast_type, COLORS["info"])

    return rx.box(
        rx.text(message, color="white", font_weight="600"),
        background=bg_color,
        color="white",
        border_radius="8px",
        padding="1rem 1.5rem",
        box_shadow="0 4px 12px rgba(0, 0, 0, 0.15)",
        position="fixed",
        top="20px",
        right="20px",
        z_index="9999",
        class_name="fade-in",
    )


def data_staleness_banner(
    has_data: bool,
    timestamp: str = "",
    hours_since: int = 0,
    banner_type: str = "info",
) -> rx.Component:
    """Banner específico para mostrar data staleness."""

    if not has_data:
        return alert_banner(
            "📭 Nenhum dado coletado ainda. Use o botão 'Atualizar Preços'.",
            "info"
        )

    if banner_type == "danger":
        message = f"""
⚠️ **ATENÇÃO: Dados desatualizados!**

Última atualização: **{timestamp}** (há **{hours_since} horas**)

Os preços exibidos podem não refletir os valores atuais dos sites.

👉 **Clique em "🔄 Atualizar Preços" para coletar preços atuais!**
"""
        return alert_banner(message, "danger")

    elif banner_type == "warning":
        message = f"""
⏰ Última atualização: **{timestamp}** (há **{hours_since} horas**)

💡 Considere atualizar os preços para ver as ofertas mais recentes!
"""
        return alert_banner(message, "warning")

    else:  # success
        message = f"✅ Dados atualizados: **{timestamp}** (há **{hours_since} horas**)"
        return alert_banner(message, "success")


def loading_spinner(text: str = "Carregando...") -> rx.Component:
    """Spinner de loading profissional."""

    return rx.center(
        rx.vstack(
            rx.spinner(
                size="3",
                color=COLORS["primary"],
            ),
            rx.text(
                text,
                font_size="1rem",
                color=COLORS["gray_500"],
                font_weight="500",
            ),
            spacing="3",
            align="center",
        ),
        padding="3rem",
        class_name="pulse",
    )


def empty_state(
    icon: str = "📭",
    title: str = "Nenhum dado encontrado",
    subtitle: str = "",
    action_button: rx.Component | None = None,
) -> rx.Component:
    """Estado vazio elegante."""

    return rx.center(
        rx.vstack(
            rx.text(icon, font_size="4rem"),
            rx.heading(title, size="6", color=COLORS["gray_700"]),
            rx.cond(
                subtitle,
                rx.text(subtitle, color=COLORS["gray_500"], text_align="center"),
                rx.fragment(),
            ),
            rx.cond(
                action_button,
                action_button,
                rx.fragment(),
            ),
            spacing="3",
            align="center",
            text_align="center",
        ),
        padding="4rem 2rem",
        class_name="fade-in",
    )
