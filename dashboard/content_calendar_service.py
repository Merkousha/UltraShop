"""Content Calendar AI Service (SO-18).

تولید تقویم محتوایی ۳۰ روزه برای شبکه‌های اجتماعی با استفاده از AI.
"""
import json
from datetime import date

IRANIAN_OCCASIONS = [
    "نوروز", "یلدا", "عید فطر", "عید قربان", "محرم", "رمضان",
    "۱۳ فروردین", "روز مادر", "روز پدر", "روز معلم", "روز دانشجو",
    "بلک فرایدی", "شب چله",
]


def _extract_json_array(raw_text: str):
    """Extract and parse a JSON array from an AI response that may include wrappers."""
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
        parsed = json.loads(text[start:end + 1])
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _build_fallback_items(store, products, target_month, days_in_month):
    """Build a deterministic calendar when AI is unavailable or returns invalid data."""
    base_products = products or ["محصولات فروشگاه"]
    slots = ["۹ صبح", "۱۲ ظهر", "۶ عصر", "۹ شب"]
    items = []

    for day in range(1, days_in_month + 1):
        product = base_products[(day - 1) % len(base_products)]
        occasion = IRANIAN_OCCASIONS[(day - 1) % len(IRANIAN_OCCASIONS)]
        weekday = target_month.replace(day=day).weekday()

        if weekday in (4, 5):
            topic = f"پیشنهاد آخرهفته: {product}"
            caption = f"این آخرهفته {product} را با یک پیشنهاد ویژه معرفی کنید و مخاطب را به خرید سریع دعوت کنید."
        elif day % 5 == 0:
            topic = f"کمپین مناسبتی {occasion}"
            caption = f"یک پست مناسبتی حول {occasion} منتشر کنید و {product} را به عنوان پیشنهاد اصلی معرفی کنید."
        elif day % 3 == 0:
            topic = f"آموزش استفاده از {product}"
            caption = f"محتوای آموزشی کوتاه درباره مزیت‌ها و روش استفاده از {product} آماده کنید."
        else:
            topic = f"معرفی محصول: {product}"
            caption = f"ویژگی‌های کلیدی {product} را با لحن ساده و کاربردی معرفی کنید و یک CTA واضح قرار دهید."

        items.append(
            {
                "day": day,
                "topic": topic,
                "caption": caption,
                "hashtags": "#فروشگاه_آنلاین #خرید_اینترنتی #پیشنهاد_ویژه",
                "suggested_time": slots[(day - 1) % len(slots)],
            }
        )

    return items


def generate_content_calendar(store, month_offset=0):
    """Generate a 30-day content calendar for the store using AI.

    Args:
        store: Store instance
        month_offset: 0 = current month, 1 = next month

    Returns:
        (entries: list[ContentCalendarEntry], target_month: date)
    """
    from core.ai_service import call_text_ai
    from core.models import ContentCalendarEntry
    from catalog.models import Product
    import calendar

    # Get active products (up to 10 names for context)
    products = list(
        Product.objects.filter(store=store, status="active")
        .values_list("name", flat=True)[:10]
    )

    # Determine target month
    today = date.today()
    if month_offset == 0:
        target_month = today.replace(day=1)
    else:
        if today.month == 12:
            target_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            target_month = today.replace(month=today.month + 1, day=1)

    days_in_month = calendar.monthrange(target_month.year, target_month.month)[1]

    prompt = f"""یک تقویم محتوایی {days_in_month} روزه برای فروشگاه آنلاین بساز.

اطلاعات فروشگاه:
- نوع کسب‌وکار: {store.description or 'فروشگاه آنلاین'}
- محصولات فعال: {', '.join(products) if products else 'متنوع'}
- ماه هدف: {target_month.strftime('%Y-%m')}

مناسبت‌های ایرانی قابل استفاده: {', '.join(IRANIAN_OCCASIONS)}

برای هر روز ({days_in_month} روز) یک پیشنهاد محتوا بساز. پاسخ را فقط به صورت JSON array برگردان:
[
  {{
    "day": 1,
    "topic": "موضوع پست",
    "caption": "متن کپشن پیشنهادی (حداکثر ۱۵۰ کلمه)",
    "hashtags": "#هشتگ۱ #هشتگ۲ #هشتگ۳",
    "suggested_time": "۹ صبح"
  }},
  ...
]
فقط JSON را برگردان، هیچ متن دیگری نزن."""

    try:
        response = call_text_ai(store=store, prompt=prompt)
        items = _extract_json_array(response)

        if not items:
            items = _build_fallback_items(store, products, target_month, days_in_month)

        # Remove existing entries for this month before re-generating
        ContentCalendarEntry.objects.filter(
            store=store,
            date__year=target_month.year,
            date__month=target_month.month,
        ).delete()

        valid_by_day = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                day = int(item.get("day", 0))
            except (TypeError, ValueError):
                continue
            if 1 <= day <= days_in_month and day not in valid_by_day:
                valid_by_day[day] = item

        # Fill missing days so generation always returns a complete month.
        if len(valid_by_day) < days_in_month:
            for fb in _build_fallback_items(store, products, target_month, days_in_month):
                day = int(fb["day"])
                if day not in valid_by_day:
                    valid_by_day[day] = fb

        entries = []
        for day in range(1, days_in_month + 1):
            item = valid_by_day[day]
            entry = ContentCalendarEntry.objects.create(
                store=store,
                date=target_month.replace(day=day),
                topic=(item.get("topic") or f"پیشنهاد محتوا برای روز {day}"),
                caption=(item.get("caption") or ""),
                hashtags=(item.get("hashtags") or ""),
                suggested_time=(item.get("suggested_time") or ""),
                is_ai_generated=True,
            )
            entries.append(entry)
        return entries, target_month

    except Exception:
        # Last resort: generate a deterministic calendar without AI.
        try:
            from core.models import ContentCalendarEntry

            ContentCalendarEntry.objects.filter(
                store=store,
                date__year=target_month.year,
                date__month=target_month.month,
            ).delete()

            fallback_items = _build_fallback_items(store, products, target_month, days_in_month)
            entries = []
            for item in fallback_items:
                entry = ContentCalendarEntry.objects.create(
                    store=store,
                    date=target_month.replace(day=int(item["day"])),
                    topic=item["topic"],
                    caption=item["caption"],
                    hashtags=item["hashtags"],
                    suggested_time=item["suggested_time"],
                    is_ai_generated=True,
                )
                entries.append(entry)
            return entries, target_month
        except Exception:
            return [], target_month
