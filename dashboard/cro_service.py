"""CRO Analyzer Service (SO-47).

تولید پیشنهادات بهینه‌سازی نرخ تبدیل (Conversion Rate Optimization) با AI.
"""
import json


def generate_cro_suggestions(store):
    """Generate CRO suggestions for the store using AI.

    Returns list of newly created CROSuggestion instances.
    """
    from core.ai_service import call_text_ai
    from core.models import CROSuggestion
    from catalog.models import Product, Category
    from orders.models import Order

    product_count = Product.objects.filter(store=store, status="active").count()
    category_count = Category.objects.filter(store=store).count()
    order_count = Order.objects.filter(store=store).count()
    paid_count = Order.objects.filter(
        store=store,
        status__in=["paid", "packed", "shipped", "delivered"],
    ).count()
    conversion = round(paid_count / order_count * 100, 1) if order_count > 0 else 0

    prompt = f"""شما یک متخصص CRO (بهینه‌سازی نرخ تبدیل) هستید.

اطلاعات فروشگاه:
- تعداد محصولات فعال: {product_count}
- تعداد دسته‌بندی‌ها: {category_count}
- نرخ تبدیل فعلی: {conversion}٪
- توضیح: {store.description or 'فروشگاه آنلاین'}

پیشنهادات بهینه‌سازی نرخ تبدیل را به صورت JSON array برگردان:
[
  {{
    "suggestion": "متن پیشنهاد به فارسی",
    "impact": "high"
  }},
  ...
]
مقدار impact باید دقیقاً یکی از سه مقدار "high"، "medium" یا "low" باشد.
حداقل ۵ و حداکثر ۱۰ پیشنهاد بده. فقط JSON برگردان."""

    try:
        response = call_text_ai(store=store, prompt=prompt)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            response = response.rsplit("```", 1)[0]
        items = json.loads(response)

        suggestions = []
        for item in items[:10]:
            impact_val = item.get("impact", "medium")
            # Validate impact value
            if impact_val not in (
                CROSuggestion.Impact.LOW,
                CROSuggestion.Impact.MEDIUM,
                CROSuggestion.Impact.HIGH,
            ):
                impact_val = CROSuggestion.Impact.MEDIUM

            s = CROSuggestion.objects.create(
                store=store,
                suggestion=item.get("suggestion", ""),
                impact=impact_val,
                status=CROSuggestion.Status.PENDING,
            )
            suggestions.append(s)
        return suggestions

    except Exception:
        return []
