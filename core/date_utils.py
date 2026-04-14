from __future__ import annotations

import datetime as _datetime
import re

import jdatetime

_DATE_RE = re.compile(r"^\s*(\d{4})[-/](\d{2})[-/](\d{2})\s*$")


def parse_jalali_or_gregorian_date(value):
    if not value:
        return None
    if isinstance(value, _datetime.date):
        return value

    text = str(value).strip()
    if not text:
        return None

    match = _DATE_RE.match(text)
    if match:
        year, month, day = (int(part) for part in match.groups())
        if year > 1600:
            try:
                return _datetime.date(year, month, day)
            except ValueError:
                return None

        try:
            return jdatetime.date(year, month, day).togregorian()
        except ValueError:
            return None

    try:
        return _datetime.date.fromisoformat(text)
    except ValueError:
        return None


def to_jalali_date_string(value, separator="-"):
    parsed = parse_jalali_or_gregorian_date(value)
    if not parsed:
        return "" if value is None else str(value)

    jalali_date = jdatetime.date.fromgregorian(date=parsed)
    return f"{jalali_date.year:04d}{separator}{jalali_date.month:02d}{separator}{jalali_date.day:02d}"