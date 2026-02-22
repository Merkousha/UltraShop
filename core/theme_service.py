import colorsys
import re


RADIUS_MAP = {
    "none": "0",
    "sm": "0.25rem",
    "md": "0.5rem",
    "lg": "0.75rem",
    "xl": "1rem",
    "full": "9999px",
}

SHADOW_MAP = {
    "none": "none",
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.15)",
}

SCALE_LIGHTNESS = {
    "50": 0.97,
    "100": 0.94,
    "200": 0.88,
    "300": 0.78,
    "400": 0.65,
    "500": None,  # input color
    "600": 0.42,
    "700": 0.35,
    "800": 0.28,
    "900": 0.20,
}


def _hex_to_hsl(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def _hsl_to_hex(h, s, l):
    l = max(0.0, min(1.0, l))
    s = max(0.0, min(1.0, s))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def generate_color_scale(hex_color):
    """Generate a 50-900 scale from a hex color (input becomes 500)."""
    h, s, l = _hex_to_hsl(hex_color)
    scale = {}
    for step, target_l in SCALE_LIGHTNESS.items():
        if target_l is None:
            scale[step] = hex_color.lower()
        else:
            scale[step] = _hsl_to_hex(h, s, target_l)
    return scale


def _relative_luminance(hex_color):
    hex_color = hex_color.lstrip("#")
    vals = []
    for i in (0, 2, 4):
        c = int(hex_color[i:i+2], 16) / 255.0
        vals.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = vals
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex1, hex2):
    """Calculate WCAG contrast ratio between two hex colors."""
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def validate_contrast(theme):
    """Return list of contrast warnings for WCAG AA (4.5:1)."""
    warnings = []
    white = "#ffffff"
    ratio_primary = contrast_ratio(theme.primary_color, white)
    if ratio_primary < 4.5:
        warnings.append(
            f"رنگ اصلی ({theme.primary_color}) روی پس‌زمینه سفید نسبت کنتراست کافی ندارد "
            f"({ratio_primary:.1f}:1 — حداقل ۴.۵:۱ لازم است)"
        )
    ratio_secondary = contrast_ratio(theme.secondary_color, white)
    if ratio_secondary < 4.5:
        warnings.append(
            f"رنگ ثانویه ({theme.secondary_color}) روی پس‌زمینه سفید نسبت کنتراست کافی ندارد "
            f"({ratio_secondary:.1f}:1 — حداقل ۴.۵:۱ لازم است)"
        )
    return warnings


def compile_store_css(store):
    """Compile full CSS variable block for a store's theme."""
    from core.models import StoreTheme
    from core.css_sanitizer import sanitize_css

    theme, _ = StoreTheme.objects.get_or_create(store=store)

    primary_scale = generate_color_scale(theme.primary_color)
    secondary_scale = generate_color_scale(theme.secondary_color)

    lines = [":root {"]

    # Primary scale
    lines.append("    /* Primary scale */")
    for step in ["50","100","200","300","400","500","600","700","800","900"]:
        lines.append(f"    --color-primary-{step}: {primary_scale[step]};")

    # Secondary scale
    lines.append("    /* Secondary scale */")
    for step in ["50","100","200","300","400","500","600","700","800","900"]:
        lines.append(f"    --color-secondary-{step}: {secondary_scale[step]};")

    # Accent
    lines.append("    /* Accent */")
    lines.append(f"    --color-accent: {theme.accent_color};")

    # Semantic tokens
    lines.append("    /* Semantic tokens */")
    lines.append("    --button-bg-primary: var(--color-primary-500);")
    lines.append("    --button-bg-primary-hover: var(--color-primary-600);")
    lines.append("    --card-bg: #ffffff;")
    lines.append("    --text-heading: var(--color-primary-900);")
    lines.append("    --text-body: #374151;")
    lines.append("    --cta-color: var(--color-accent);")

    # Component tokens
    lines.append("    /* Component tokens */")
    lines.append("    --btn-primary-bg: var(--button-bg-primary);")
    lines.append("    --btn-primary-hover: var(--button-bg-primary-hover);")
    lines.append("    --input-border-focus: var(--color-primary-500);")
    lines.append("    --badge-success-bg: #10b981;")

    # Typography
    lines.append("    /* Typography */")
    lines.append(f"    --font-heading: '{theme.heading_font}', Tahoma, sans-serif;")
    lines.append(f"    --font-body: '{theme.body_font}', Tahoma, sans-serif;")

    # Spacing tokens
    lines.append("    /* Spacing */")
    lines.append(f"    --radius-base: {RADIUS_MAP.get(theme.radius_scale, '0.5rem')};")
    lines.append(f"    --shadow-base: {SHADOW_MAP.get(theme.shadow_level, 'none')};")

    lines.append("}")

    css = "\n".join(lines)

    # Append sanitized custom CSS
    if theme.custom_css:
        sanitized, _ = sanitize_css(theme.custom_css)
        if sanitized:
            css += "\n\n" + sanitized

    return css
