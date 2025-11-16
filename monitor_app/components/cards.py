"""Componentes de Cards."""

import reflex as rx
from ..styles import METRIC_CARD_STYLE, CARD_STYLE, CARD_GRADIENT_STYLE, COLORS, GRADIENTS


def metric_card(
    label: str,
    value: str | int | float,
    icon: str = "📊",
    delta: str | None = None,
    gradient: bool = False,
) -> rx.Component:
    """Card de métrica profissional."""

    style = CARD_GRADIENT_STYLE if gradient else METRIC_CARD_STYLE

    return rx.box(
        rx.vstack(
            rx.text(icon, font_size="2rem"),
            rx.heading(str(value), size="8", font_weight="bold"),
            rx.text(label, font_size="0.9rem", opacity="0.9"),
            rx.cond(
                delta,
                rx.text(delta, font_size="0.85rem", color=COLORS["success"]),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
        ),
        **style,
        class_name="fade-in",
    )


def product_card(
    product_name: str,
    store: str,
    price: float,
    desired_price: float | None = None,
    url: str = "",
    trend: str = "",
    category: str = "",
) -> rx.Component:
    """Card de produto."""

    savings = desired_price - price if desired_price and price <= desired_price else 0
    savings_percent = (
        (savings / desired_price) * 100 if desired_price and savings > 0 else 0
    )

    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.heading(product_name, size="4", font_weight="600"),
                    rx.text(
                        f"🏪 {store.upper()}",
                        font_size="0.85rem",
                        color=COLORS["gray_500"],
                    ),
                    spacing="1",
                    align_items="start",
                    flex="1",
                ),
                rx.cond(
                    trend,
                    rx.text(trend, font_size="0.85rem"),
                    rx.fragment(),
                ),
                width="100%",
                justify="between",
            ),
            # Preço
            rx.hstack(
                rx.vstack(
                    rx.text("Preço Atual", font_size="0.8rem", color=COLORS["gray_500"]),
                    rx.heading(
                        f"R$ {price:.2f}",
                        size="6",
                        color=COLORS["primary"],
                        font_weight="bold",
                    ),
                    spacing="0",
                    align_items="start",
                ),
                rx.cond(
                    desired_price,
                    rx.vstack(
                        rx.text("Meta", font_size="0.8rem", color=COLORS["gray_500"]),
                        rx.text(
                            f"R$ {desired_price:.2f}",
                            font_size="1rem",
                            font_weight="600",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    savings > 0,
                    rx.vstack(
                        rx.text("Economia", font_size="0.8rem", color=COLORS["gray_500"]),
                        rx.text(
                            f"R$ {savings:.2f} ({savings_percent:.1f}%)",
                            font_size="1rem",
                            font_weight="600",
                            color=COLORS["success"],
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                justify="between",
            ),
            # Botão
            rx.cond(
                url,
                rx.link(
                    rx.button(
                        "🛒 Ver Oferta",
                        bg=GRADIENTS["primary"],
                        color="white",
                        border_radius="8px",
                        width="100%",
                        _hover={"transform": "scale(1.02)"},
                    ),
                    href=url,
                    is_external=True,
                ),
                rx.fragment(),
            ),
            spacing="4",
            width="100%",
        ),
        **CARD_STYLE,
        class_name="fade-in",
    )


def highlight_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "🎯",
    color: str = "success",
) -> rx.Component:
    """Card de destaque (para alertas de ofertas)."""

    gradient_map = {
        "success": GRADIENTS["success"],
        "warning": GRADIENTS["warning"],
        "danger": GRADIENTS["danger"],
        "primary": GRADIENTS["primary"],
    }

    gradient = gradient_map.get(color, GRADIENTS["primary"])

    return rx.box(
        rx.vstack(
            rx.text(icon, font_size="1.5rem"),
            rx.heading(title, size="3", font_weight="600", text_align="center"),
            rx.heading(value, size="7", font_weight="bold", text_align="center"),
            rx.cond(
                subtitle,
                rx.text(subtitle, font_size="0.9rem", opacity="0.9", text_align="center"),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
        ),
        background=gradient,
        color="white",
        border_radius="12px",
        padding="1.5rem",
        text_align="center",
        box_shadow="0 4px 6px rgba(0, 0, 0, 0.1)",
        class_name="fade-in",
    )


def stat_card(
    category: str,
    count: int,
    active: int,
    total_price: float,
    color: str = "#667eea",
) -> rx.Component:
    """Card de estatísticas por categoria."""

    avg_price = total_price / count if count > 0 else 0

    return rx.box(
        rx.vstack(
            rx.heading(category.upper(), size="4", font_weight="600"),
            rx.hstack(
                rx.vstack(
                    rx.text("Total", font_size="0.8rem", color=COLORS["gray_500"]),
                    rx.text(str(count), font_size="1.5rem", font_weight="bold"),
                    spacing="0",
                ),
                rx.vstack(
                    rx.text("Ativos", font_size="0.8rem", color=COLORS["gray_500"]),
                    rx.text(str(active), font_size="1.5rem", font_weight="bold"),
                    spacing="0",
                ),
                rx.vstack(
                    rx.text("Preço Médio", font_size="0.8rem", color=COLORS["gray_500"]),
                    rx.text(
                        f"R$ {avg_price:.2f}",
                        font_size="1.2rem",
                        font_weight="bold",
                    ),
                    spacing="0",
                ),
                justify="between",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        **CARD_STYLE,
        border_left=f"4px solid {color}",
        class_name="fade-in",
    )
