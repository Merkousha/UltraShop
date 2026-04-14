import re
from decimal import Decimal

from django import template

register = template.Library()

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _group_digits(int_part: str) -> str:
    sign = ""
    if int_part.startswith("-"):
        sign = "-"
        int_part = int_part[1:]
    rev = int_part[::-1]
    grouped = "٬".join(rev[i:i + 3] for i in range(0, len(rev), 3))[::-1]
    return sign + grouped


@register.filter
def persian_number(value):
    if value is None:
        return ""

    if isinstance(value, (int, Decimal, float)):
        text = str(value)
    else:
        text = str(value).strip()

    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        if "." in text:
            int_part, frac = text.split(".", 1)
            grouped = _group_digits(int_part)
            text = f"{grouped}.{frac}"
        else:
            text = _group_digits(text)

    return text.translate(_PERSIAN_DIGITS)