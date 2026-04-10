from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Lookup a dictionary value by key in templates: {{ my_dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0


@register.simple_tag
def store_theme_css(store):
    """Output <style> block with compiled CSS variables for the store."""
    from core.theme_service import compile_store_css
    try:
        css = compile_store_css(store)
    except Exception:
        css = ""
    return mark_safe(f"<style>\n{css}\n</style>")


@register.simple_tag
def store_custom_css(store):
    """Output <style> block with store's custom CSS (sanitized)."""
    from core.css_sanitizer import sanitize_css
    try:
        theme = store.theme
        if theme.custom_css:
            sanitized, _ = sanitize_css(theme.custom_css)
            return mark_safe(f"<style>\n{sanitized}\n</style>")
    except Exception:
        pass
    return mark_safe("")
