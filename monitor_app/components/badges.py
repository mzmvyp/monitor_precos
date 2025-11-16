"""Componentes de Badges."""

import reflex as rx
from ..styles import BADGE_STYLE, COLORS, CATEGORY_EMOJIS


def badge(
    text: str,
    badge_type: str = "info",  # success, warning, danger, info
    icon: str = "",
) -> rx.Component:
    """Badge simples."""

    style = BADGE_STYLE.get(badge_type, BADGE_STYLE["info"])

    return rx.box(
        rx.text(
            f"{icon} {text}" if icon else text,
        ),
        **style,
    )


def status_badge(enabled: bool) -> rx.Component:
    """Badge de status (ativo/inativo)."""

    if enabled:
        return badge("Ativo", "success", "✅")
    else:
        return badge("Inativo", "danger", "❌")


def category_badge(category: str, color: str = "") -> rx.Component:
    """Badge de categoria com emoji e cor personalizada."""

    emoji = CATEGORY_EMOJIS.get(category, "📦")
    bg_color = color or COLORS.get(category, COLORS["gray_500"])

    return rx.box(
        rx.text(f"{emoji} {category.upper()}"),
        background=bg_color,
        color="white",
        padding="0.5rem 1rem",
        border_radius="20px",
        font_size="0.85rem",
        font_weight="600",
        display="inline-block",
        class_name="fade-in",
    )


def price_trend_badge(trend: str) -> rx.Component:
    """Badge de tendência de preço."""

    if "🟢" in trend:  # Queda
        return badge(trend, "success")
    elif "🔴" in trend:  # Aumento
        return badge(trend, "danger")
    elif "🟡" in trend:  # Estável/Novo
        return badge(trend, "warning")
    else:  # N/A
        return badge(trend, "info")


def store_badge(store: str) -> rx.Component:
    """Badge de loja."""

    store_colors = {
        "kabum": "#FF6500",
        "amazon": "#FF9900",
        "pichau": "#00A8E1",
        "mercadolivre": "#FFE600",
        "royal_caribbean": "#002E5D",
        "other": COLORS["gray_500"],
    }

    color = store_colors.get(store.lower(), COLORS["info"])

    return rx.box(
        rx.text(f"🏪 {store.upper()}"),
        background=color,
        color="white",
        padding="0.25rem 0.75rem",
        border_radius="6px",
        font_size="0.8rem",
        font_weight="600",
        display="inline-block",
    )
