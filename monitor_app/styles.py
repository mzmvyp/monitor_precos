"""Design System - Estilos profissionais para o Monitor de Preços."""

import reflex as rx

# ============================================================
# CORES DO SISTEMA (Design System)
# ============================================================

COLORS = {
    # Principais
    "primary": "#667eea",
    "primary_dark": "#764ba2",
    "secondary": "#0ea5e9",

    # Status
    "success": "#10b981",
    "success_dark": "#059669",
    "warning": "#f59e0b",
    "warning_dark": "#d97706",
    "danger": "#ef4444",
    "danger_dark": "#dc2626",
    "info": "#3b82f6",

    # Neutros
    "gray_50": "#f9fafb",
    "gray_100": "#f3f4f6",
    "gray_200": "#e5e7eb",
    "gray_300": "#d1d5db",
    "gray_500": "#6b7280",
    "gray_700": "#374151",
    "gray_900": "#111827",

    # Backgrounds
    "bg_primary": "#ffffff",
    "bg_secondary": "#f9fafb",
    "bg_dark": "#1f2937",

    # Categorias (Produtos)
    "cpu": "#FF6B6B",
    "motherboard": "#4ECDC4",
    "memory": "#45B7D1",
    "storage": "#96CEB4",
    "gpu": "#DDA15E",
    "psu": "#BC6C25",
    "cooler": "#588157",
    "case": "#6C757D",
    "cruise": "#E63946",
    "other": "#495057",
}

# ============================================================
# GRADIENTES
# ============================================================

GRADIENTS = {
    "primary": f"linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%)",
    "success": f"linear-gradient(135deg, {COLORS['success']} 0%, {COLORS['success_dark']} 100%)",
    "warning": f"linear-gradient(135deg, {COLORS['warning']} 0%, {COLORS['warning_dark']} 100%)",
    "danger": f"linear-gradient(135deg, {COLORS['danger']} 0%, {COLORS['danger_dark']} 100%)",
}

# ============================================================
# ESTILOS DE COMPONENTES REUTILIZÁVEIS
# ============================================================

# Estilo base para cards
CARD_STYLE = {
    "background": COLORS["bg_primary"],
    "border_radius": "12px",
    "padding": "1.5rem",
    "box_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "border": f"1px solid {COLORS['gray_200']}",
}

# Estilo para card com gradiente
CARD_GRADIENT_STYLE = {
    "background": GRADIENTS["primary"],
    "border_radius": "12px",
    "padding": "1.5rem",
    "box_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "color": "white",
}

# Estilo para métricas
METRIC_CARD_STYLE = {
    "background": COLORS["bg_primary"],
    "border_radius": "10px",
    "padding": "1.25rem",
    "box_shadow": "0 2px 4px rgba(0, 0, 0, 0.05)",
    "border": f"1px solid {COLORS['gray_200']}",
    "text_align": "center",
}

# Estilo para botões primários
BUTTON_PRIMARY_STYLE = {
    "background": GRADIENTS["primary"],
    "color": "white",
    "border_radius": "8px",
    "padding": "0.75rem 1.5rem",
    "font_weight": "600",
    "border": "none",
    "cursor": "pointer",
    "transition": "all 0.2s",
    "_hover": {
        "transform": "translateY(-2px)",
        "box_shadow": "0 4px 8px rgba(0, 0, 0, 0.2)",
    },
}

# Estilo para botões secundários
BUTTON_SECONDARY_STYLE = {
    "background": COLORS["bg_secondary"],
    "color": COLORS["gray_700"],
    "border_radius": "8px",
    "padding": "0.75rem 1.5rem",
    "font_weight": "600",
    "border": f"1px solid {COLORS['gray_300']}",
    "cursor": "pointer",
    "transition": "all 0.2s",
    "_hover": {
        "background": COLORS["gray_100"],
    },
}

# Estilo para inputs
INPUT_STYLE = {
    "border_radius": "8px",
    "border": f"1px solid {COLORS['gray_300']}",
    "padding": "0.75rem 1rem",
    "font_size": "0.95rem",
    "width": "100%",
    "_focus": {
        "border_color": COLORS["primary"],
        "outline": "none",
        "box_shadow": f"0 0 0 3px rgba(102, 126, 234, 0.1)",
    },
}

# Estilo para badges
BADGE_STYLE = {
    "success": {
        "background": COLORS["success"],
        "color": "white",
        "padding": "0.25rem 0.75rem",
        "border_radius": "20px",
        "font_size": "0.85rem",
        "font_weight": "600",
        "display": "inline-block",
    },
    "warning": {
        "background": COLORS["warning"],
        "color": "white",
        "padding": "0.25rem 0.75rem",
        "border_radius": "20px",
        "font_size": "0.85rem",
        "font_weight": "600",
        "display": "inline-block",
    },
    "danger": {
        "background": COLORS["danger"],
        "color": "white",
        "padding": "0.25rem 0.75rem",
        "border_radius": "20px",
        "font_size": "0.85rem",
        "font_weight": "600",
        "display": "inline-block",
    },
    "info": {
        "background": COLORS["info"],
        "color": "white",
        "padding": "0.25rem 0.75rem",
        "border_radius": "20px",
        "font_size": "0.85rem",
        "font_weight": "600",
        "display": "inline-block",
    },
}

# Estilo para container principal
CONTAINER_STYLE = {
    "max_width": "1400px",
    "margin": "0 auto",
    "padding": "2rem 1rem",
}

# Estilo para header
HEADER_STYLE = {
    "background": GRADIENTS["primary"],
    "color": "white",
    "padding": "2rem 1rem",
    "margin_bottom": "2rem",
    "box_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
}

# Estilo para tabelas
TABLE_STYLE = {
    "width": "100%",
    "border_collapse": "collapse",
    "background": COLORS["bg_primary"],
    "border_radius": "8px",
    "overflow": "hidden",
    "box_shadow": "0 2px 4px rgba(0, 0, 0, 0.05)",
}

TABLE_HEADER_STYLE = {
    "background": COLORS["gray_100"],
    "padding": "1rem",
    "text_align": "left",
    "font_weight": "600",
    "color": COLORS["gray_700"],
    "border_bottom": f"2px solid {COLORS['gray_300']}",
}

TABLE_CELL_STYLE = {
    "padding": "1rem",
    "border_bottom": f"1px solid {COLORS['gray_200']}",
}

# Estilo para alertas/banners
ALERT_STYLE = {
    "success": {
        "background": "#d1fae5",
        "border": f"1px solid {COLORS['success']}",
        "color": "#065f46",
        "padding": "1rem 1.5rem",
        "border_radius": "8px",
        "margin_bottom": "1rem",
    },
    "warning": {
        "background": "#fef3c7",
        "border": f"1px solid {COLORS['warning']}",
        "color": "#92400e",
        "padding": "1rem 1.5rem",
        "border_radius": "8px",
        "margin_bottom": "1rem",
    },
    "danger": {
        "background": "#fee2e2",
        "border": f"1px solid {COLORS['danger']}",
        "color": "#991b1b",
        "padding": "1rem 1.5rem",
        "border_radius": "8px",
        "margin_bottom": "1rem",
    },
    "info": {
        "background": "#dbeafe",
        "border": f"1px solid {COLORS['info']}",
        "color": "#1e3a8a",
        "padding": "1rem 1.5rem",
        "border_radius": "8px",
        "margin_bottom": "1rem",
    },
}

# ============================================================
# RESPONSIVIDADE
# ============================================================

BREAKPOINTS = {
    "mobile": "640px",
    "tablet": "768px",
    "desktop": "1024px",
    "wide": "1280px",
}

# ============================================================
# TIPOGRAFIA
# ============================================================

TYPOGRAPHY = {
    "h1": {
        "font_size": "2.5rem",
        "font_weight": "700",
        "line_height": "1.2",
        "margin_bottom": "1rem",
    },
    "h2": {
        "font_size": "2rem",
        "font_weight": "600",
        "line_height": "1.3",
        "margin_bottom": "0.875rem",
    },
    "h3": {
        "font_size": "1.5rem",
        "font_weight": "600",
        "line_height": "1.4",
        "margin_bottom": "0.75rem",
    },
    "h4": {
        "font_size": "1.25rem",
        "font_weight": "600",
        "line_height": "1.4",
        "margin_bottom": "0.625rem",
    },
    "body": {
        "font_size": "1rem",
        "line_height": "1.6",
        "color": COLORS["gray_700"],
    },
    "small": {
        "font_size": "0.875rem",
        "line_height": "1.5",
        "color": COLORS["gray_500"],
    },
}

# ============================================================
# EMOJIS POR CATEGORIA
# ============================================================

CATEGORY_EMOJIS = {
    "cpu": "🖥️",
    "gpu": "🎮",
    "motherboard": "⚡",
    "memory": "💾",
    "storage": "💿",
    "psu": "🔌",
    "cooler": "❄️",
    "case": "📦",
    "cruise": "🚢",
    "other": "📦",
}

# ============================================================
# ANIMAÇÕES (CSS)
# ============================================================

ANIMATIONS = """
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { transform: translateX(-10px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.fade-in {
    animation: fadeIn 0.3s ease-in-out;
}

.slide-in {
    animation: slideIn 0.3s ease-in-out;
}

.pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
"""
