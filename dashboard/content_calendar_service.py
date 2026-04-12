"""Content Calendar AI Service (SO-18).

تولید تقویم محتوایی ۳۰ روزه برای شبکه‌های اجتماعی با استفاده از AI.
"""
import json

IRANIAN_OCCASIONS = [
    "نوروز", "یلدا", "عید فطر", "عید قربان", "محرم", "رمضان",
    "۱۳ فروردین", "روز مادر", "روز پدر", "روز معلم", "روز دانشجو",
    "بلک فرایدی", "شب چله",
]


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
    from datetime import date
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

    prompt = f"""یک تقویم محتوایی ۳۰ روزه برای فروشگاه آنلاین بساز.

اطلاعات فروشگاه:
- نوع کسب‌وکار: {store.description or 'فروشگاه آنلاین'}
- محصولات فعال: {', '.join(products) if products else 'متنوع'}
- ماه هدف: {target_month.strftime('%Y-%m')}

مناسبت‌های ایرانی قابل استفاده: {', '.join(IRANIAN_OCCASIONS)}

برای هر روز (30 روز) یک پیشنهاد محتوا بساز. پاسخ را فقط به صورت JSON array برگردان:
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
        # Strip possible markdown code blocks
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            response = response.rsplit("```", 1)[0]
        items = json.loads(response)

        # Remove existing entries for this month before re-generating
        ContentCalendarEntry.objects.filter(
            store=store,
            date__year=target_month.year,
            date__month=target_month.month,
        ).delete()

        entries = []
        for item in items[:30]:
            day = int(item.get("day", 1))
            if day < 1 or day > days_in_month:
                continue
            entry = ContentCalendarEntry.objects.create(
                store=store,
                date=target_month.replace(day=day),
                topic=item.get("topic", ""),
                caption=item.get("caption", ""),
                hashtags=item.get("hashtags", ""),
                suggested_time=item.get("suggested_time", ""),
                is_ai_generated=True,
            )
            entries.append(entry)
        return entries, target_month

    except Exception:
        return [], target_month
