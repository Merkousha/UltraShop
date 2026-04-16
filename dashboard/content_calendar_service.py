"""Content Calendar AI Service - with robust AI parsing and fallback."""

import json
import logging
from datetime import date
from typing import Dict, List

logger = logging.getLogger(__name__)


def _fetch_time_ir(year: int, month: int) -> Dict[int, List[str]]:
    """Fetch occasions for a Jalali month from time.ir API."""
    try:
        import requests
        import ssl
        from requests.adapters import HTTPAdapter
        
        class SSLAdapter(HTTPAdapter):
            """Custom adapter with relaxed SSL requirements."""
            def init_poolmanager(self, *args, **kwargs):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                kwargs['ssl_context'] = ctx
                return super().init_poolmanager(*args, **kwargs)

        url = f"https://api.time.ir/v1/event/fa/events/calendar?year={year}&month={month}&day=0&base1=0&base2=1&base3=2"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        session.mount('http://', HTTPAdapter())
        
        response = session.get(
            url,
            headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        occasions_by_day: Dict[int, List[str]] = {}

        if not (isinstance(data, dict) and data.get("status_code") == 200):
            logger.warning("time.ir API returned status %s", data.get("status_code"))
            return {}

        event_list = data.get("data", {}).get("event_list", [])
        for event in event_list:
            try:
                if not isinstance(event, dict):
                    continue
                title = event.get("title", "").strip()
                if not title:
                    continue
                jalali_day = event.get("jalali_day")
                jalali_month = event.get("jalali_month")
                if not (jalali_day and jalali_month and jalali_month == month):
                    continue
                if not (1 <= jalali_day <= 31):
                    continue
                occasions_by_day.setdefault(jalali_day, []).append(title)
            except Exception:
                continue

        return occasions_by_day
    except Exception as exc:
        logger.warning("time.ir API fetch failed for %s/%s: %s", year, month, exc)
        return {}


SOLAR_OCCASIONS = {
    (1, 1): "نوروز",
    (1, 12): "روز جمهوری اسلامی",
    (1, 13): "سیزده‌به‌در",
    (3, 5): "رحلت امام خمینی",
    (3, 13): "قیام ۱۵ خرداد",
    (5, 1): "روز کارگر",
    (10, 19): "روز مادر",
}

_OCCASION_CACHE: Dict[tuple, Dict[int, List[str]]] = {}


def get_occ(month: int, day: int, year: int = None) -> str:
    """Get occasion text for one Jalali date."""
    if year is None:
        import jdatetime

        year = jdatetime.date.today().year

    key = (year, month)
    if key not in _OCCASION_CACHE:
        _OCCASION_CACHE[key] = _fetch_time_ir(year, month)

    dynamic = _OCCASION_CACHE[key]
    if day in dynamic:
        return " / ".join(dynamic[day])
    return SOLAR_OCCASIONS.get((month, day), "")


def get_occs(month: int, year: int = None) -> List[str]:
    """Get all occasions for one Jalali month."""
    if year is None:
        import jdatetime

        year = jdatetime.date.today().year

    key = (year, month)
    if key not in _OCCASION_CACHE:
        _OCCASION_CACHE[key] = _fetch_time_ir(year, month)

    dynamic = _OCCASION_CACHE[key]
    results: List[str] = []
    for day in sorted(dynamic.keys()):
        for occasion in dynamic[day]:
            results.append(f"{day}/{month}: {occasion}")

    for (m, d), occasion in SOLAR_OCCASIONS.items():
        if m == month and d not in dynamic:
            results.append(f"{d}/{month}: {occasion}")

    try:
        results.sort(key=lambda item: int(item.split("/")[0]))
    except Exception:
        pass
    return results


def _extract_json_array(raw_text: str) -> List[dict]:
    """Extract a JSON array even when model wraps it in prose/markdown."""
    text = (raw_text or "").strip()
    if not text:
        return []

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _build_fallback_items(products: List[str], target_month: date, days: int) -> List[dict]:
    """Build complete non-empty fallback content for all days."""
    import jdatetime

    product_list = products or ["محصولات فروشگاه"]
    time_slots = ["۹ صبح", "۱۲ ظهر", "۶ عصر", "۹ شب"]
    items: List[dict] = []

    for day in range(1, days + 1):
        product_name = product_list[(day - 1) % len(product_list)]
        g_date = target_month.replace(day=day)
        j_date = jdatetime.date.fromgregorian(date=g_date)
        occasion = get_occ(j_date.month, j_date.day, j_date.year)

        if occasion:
            topic = f"کمپین مناسبتی {occasion}: معرفی {product_name}"
            caption = (
                f"امروز به مناسبت {occasion} یک پست موضوعی منتشر کنید و {product_name} را "
                "با یک پیشنهاد محدود و CTA واضح معرفی کنید."
            )
        elif g_date.weekday() in (4, 5):
            topic = f"پیشنهاد آخرهفته برای {product_name}"
            caption = (
                f"برای آخرهفته یک سناریوی فروش سریع بچینید: مزیت اصلی {product_name} را بگویید "
                "و مخاطب را به اقدام فوری دعوت کنید."
            )
        elif day % 5 == 0:
            topic = f"آموزش استفاده از {product_name}"
            caption = f"یک محتوای آموزشی کوتاه درباره کاربرد و روش استفاده از {product_name} منتشر کنید."
        elif day % 3 == 0:
            topic = f"مقایسه و معرفی {product_name}"
            caption = (
                f"در قالب پست مقایسه‌ای، ویژگی‌های {product_name} را نسبت به گزینه‌های مشابه نشان دهید "
                "و دلیل خرید را شفاف کنید."
            )
        else:
            topic = f"پیشنهاد روز برای {product_name}"
            caption = (
                f"یک پست کوتاه و جذاب برای {product_name} آماده کنید: مشکل مشتری را مطرح کنید، "
                "راه‌حل محصول را بگویید و یک CTA اضافه کنید."
            )

        items.append(
            {
                "day": day,
                "topic": topic,
                "caption": caption,
                "hashtags": "#فروشگاه_آنلاین #خرید_اینترنتی #پیشنهاد_ویژه",
                "suggested_time": time_slots[(day - 1) % len(time_slots)],
            }
        )

    return items


def generate_content_calendar(store, month_offset=0):
    """Generate monthly content calendar via AI with resilient fallback."""
    from catalog.models import Product
    from core.ai_service import call_text_ai
    from catalog.models import ContentCalendarEntry
    import calendar
    import jdatetime

    products = list(
        Product.objects.filter(store=store, status="active").values_list("name", flat=True)[:10]
    )

    today = date.today()
    if int(month_offset or 0) <= 0:
        target_month = today.replace(day=1)
    else:
        month = today.month + int(month_offset)
        year = today.year
        while month > 12:
            month -= 12
            year += 1
        target_month = date(year, month, 1)

    days = calendar.monthrange(target_month.year, target_month.month)[1]
    j_date = jdatetime.date.fromgregorian(date=target_month)
    month_occasions = get_occs(j_date.month, j_date.year)
    occasions_text = "\n".join(month_occasions[:20]) if month_occasions else "مناسبت خاصی ثبت نشده است"

    prompt = f"""برای یک فروشگاه اینترنتی فارسی، تقویم محتوایی {days} روزه بساز.

اطلاعات:
- ماه هدف (شمسی): {j_date.year}/{j_date.month:02d}
- محصولات فعال: {', '.join(products) if products else 'محصولات متنوع'}

مناسبت‌های این ماه:
{occasions_text}

خروجی را فقط به صورت JSON array برگردان. برای هر روز یک آیتم با کلیدهای زیر:
- day: عدد روز ماه (۱ تا {days})
- topic: موضوع دقیق پست (غیرخالی)
- caption: کپشن پیشنهادی (حداقل یک جمله)
- hashtags: چند هشتگ مرتبط
- suggested_time: زمان پیشنهادی (مثل ۹ صبح)

هیچ متن اضافه‌ای خارج از JSON ننویس."""

    ai_items: List[dict] = []
    ai_days = set()
    try:
        ai_response = call_text_ai(store=store, prompt=prompt)
        parsed_items = _extract_json_array(ai_response)
        for item in parsed_items:
            if not isinstance(item, dict):
                continue
            try:
                day = int(item.get("day", 0))
            except (TypeError, ValueError):
                continue
            if 1 <= day <= days:
                ai_items.append(item)
                ai_days.add(day)
    except Exception as exc:
        logger.warning("AI calendar generation failed for store=%s: %s", getattr(store, "id", None), exc)

    fallback_items = _build_fallback_items(products, target_month, days)
    fallback_by_day = {int(item["day"]): item for item in fallback_items}
    ai_by_day = {}
    for item in ai_items:
        try:
            ai_by_day[int(item.get("day", 0))] = item
        except (TypeError, ValueError):
            continue

    ContentCalendarEntry.objects.filter(
        store=store,
        date__year=target_month.year,
        date__month=target_month.month,
    ).delete()

    entries = []
    for day in range(1, days + 1):
        fb = fallback_by_day[day]
        ai = ai_by_day.get(day, {})

        topic = (ai.get("topic") or "").strip() if isinstance(ai, dict) else ""
        caption = (ai.get("caption") or "").strip() if isinstance(ai, dict) else ""
        hashtags = (ai.get("hashtags") or "").strip() if isinstance(ai, dict) else ""
        suggested_time = (ai.get("suggested_time") or "").strip() if isinstance(ai, dict) else ""

        used_ai = bool(topic or caption or hashtags or suggested_time)

        entry = ContentCalendarEntry.objects.create(
            store=store,
            date=target_month.replace(day=day),
            topic=topic or fb["topic"],
            caption=caption or fb["caption"],
            hashtags=hashtags or fb["hashtags"],
            suggested_time=suggested_time or fb["suggested_time"],
            is_ai_generated=used_ai,
        )
        entries.append(entry)

    return entries, target_month


def generate(store, month_offset=0):
    """Backward-compatible alias."""
    return generate_content_calendar(store, month_offset)
