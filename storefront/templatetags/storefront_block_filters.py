import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def _sanitize_block_html(html: str) -> str:
    """Remove script, event handlers, javascript: from HTML for custom block (SO-46 security)."""
    if not html:
        return ""
    # Remove <script>...</script>
    html = re.sub(r"<script[\s\S]*?</script\s*>", "", html, flags=re.IGNORECASE)
    # Remove on* attributes
    html = re.sub(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+on\w+\s*=\s*[^\s>]+", "", html, flags=re.IGNORECASE)
    # Remove javascript: in href/src
    html = re.sub(r"javascript\s*:", "", html, flags=re.IGNORECASE)
    return html.strip()


@register.filter
def sanitize_block_html(html):
    return mark_safe(_sanitize_block_html(html or ""))
