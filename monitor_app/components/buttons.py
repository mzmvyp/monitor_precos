"""Componentes de Botões."""

import reflex as rx
from ..styles import BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE, COLORS, GRADIENTS


def primary_button(
    text: str,
    icon: str = "",
    on_click=None,
    width: str = "auto",
    disabled: bool = False,
) -> rx.Component:
    """Botão primário com gradiente."""

    display_text = f"{icon} {text}" if icon else text

    return rx.button(
        display_text,
        on_click=on_click,
        **{**BUTTON_PRIMARY_STYLE, "width": width},
        disabled=disabled,
        opacity="0.5" if disabled else "1",
        cursor="not-allowed" if disabled else "pointer",
    )


def secondary_button(
    text: str,
    icon: str = "",
    on_click=None,
    width: str = "auto",
    disabled: bool = False,
) -> rx.Component:
    """Botão secundário."""

    display_text = f"{icon} {text}" if icon else text

    return rx.button(
        display_text,
        on_click=on_click,
        **{**BUTTON_SECONDARY_STYLE, "width": width},
        disabled=disabled,
        opacity="0.5" if disabled else "1",
        cursor="not-allowed" if disabled else "pointer",
    )


def icon_button(
    icon: str,
    on_click=None,
    tooltip: str = "",
    variant: str = "ghost",  # ghost, solid
    color: str = "primary",
) -> rx.Component:
    """Botão somente com ícone."""

    color_map = {
        "primary": COLORS["primary"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger": COLORS["danger"],
    }

    bg_color = color_map.get(color, COLORS["primary"]) if variant == "solid" else "transparent"

    button = rx.button(
        icon,
        background=bg_color,
        color="white" if variant == "solid" else color_map.get(color, COLORS["primary"]),
        border_radius="50%",
        width="40px",
        height="40px",
        padding="0",
        border="none",
        cursor="pointer",
        font_size="1.2rem",
        _hover={
            "transform": "scale(1.1)",
            "background": color_map.get(color, COLORS["primary"]) if variant == "ghost" else bg_color,
            "color": "white" if variant == "ghost" else "white",
        },
        transition="all 0.2s",
        on_click=on_click,
    )

    if tooltip:
        return rx.tooltip(button, label=tooltip)

    return button


def link_button(
    text: str,
    url: str,
    icon: str = "🔗",
    external: bool = True,
) -> rx.Component:
    """Botão que funciona como link."""

    return rx.link(
        rx.button(
            f"{icon} {text}",
            **BUTTON_PRIMARY_STYLE,
            width="100%",
        ),
        href=url,
        is_external=external,
    )


def action_button_group(
    buttons: list[dict],
) -> rx.Component:
    """Grupo de botões de ação."""

    return rx.hstack(
        *[
            icon_button(
                icon=btn.get("icon", ""),
                on_click=btn.get("on_click"),
                tooltip=btn.get("tooltip", ""),
                variant=btn.get("variant", "ghost"),
                color=btn.get("color", "primary"),
            )
            for btn in buttons
        ],
        spacing="2",
    )


def download_button(
    text: str,
    data: str,
    filename: str,
    mime_type: str = "text/plain",
    icon: str = "⬇️",
) -> rx.Component:
    """Botão de download."""

    return rx.download(
        rx.button(
            f"{icon} {text}",
            **BUTTON_PRIMARY_STYLE,
        ),
        data=data,
        filename=filename,
        mime_type=mime_type,
    )
