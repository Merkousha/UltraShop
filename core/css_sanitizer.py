import re

MAX_CSS_SIZE = 50 * 1024  # 50kb


def sanitize_css(css: str) -> tuple[str, list[str]]:
    """
    Sanitize custom CSS input.
    Returns (sanitized_css, warnings_list).
    """
    warnings = []

    if len(css.encode("utf-8")) > MAX_CSS_SIZE:
        warnings.append("CSS بیش از ۵۰ کیلوبایت است. محتوای اضافه حذف شد.")
        css = css.encode("utf-8")[:MAX_CSS_SIZE].decode("utf-8", errors="ignore")

    # Remove <script> tags
    if re.search(r"<script", css, re.IGNORECASE):
        warnings.append("تگ‌های اسکریپت از CSS حذف شدند.")
        css = re.sub(r"<script[\s\S]*?</script[^>]*>", "", css, flags=re.IGNORECASE)

    # Remove javascript: references
    if re.search(r"javascript\s*:", css, re.IGNORECASE):
        warnings.append("ارجاعات javascript: از CSS حذف شدند.")
        css = re.sub(r"javascript\s*:[^;\"'}\s]*", "", css, flags=re.IGNORECASE)

    # Remove expression()
    if re.search(r"expression\s*\(", css, re.IGNORECASE):
        warnings.append("تابع expression() از CSS حذف شد.")
        css = re.sub(r"expression\s*\([^)]*\)", "", css, flags=re.IGNORECASE)

    # Remove @import with external URLs (must run before url() stripping)
    import_pattern = re.compile(
        r'@import\s+(?:url\s*\(\s*)?["\']?\s*(?:https?://|ftp://)[^;)\'"]*["\']?\s*\)?\s*;?',
        re.IGNORECASE,
    )
    if import_pattern.search(css):
        warnings.append("قوانین @import خارجی از CSS حذف شدند.")
        css = import_pattern.sub("", css)

    # Remove url() with external domains (http/https/ftp)
    external_url_pattern = re.compile(
        r'url\s*\(\s*["\']?\s*(https?://|ftp://)[^)\'"]+["\']?\s*\)',
        re.IGNORECASE,
    )
    if external_url_pattern.search(css):
        warnings.append("لینک‌های خارجی در url() از CSS حذف شدند.")
        css = external_url_pattern.sub("", css)

    return css.strip(), warnings
