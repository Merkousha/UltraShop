"""CFO Agent Service (SO-36)."""


def generate_cfo_report(store):
    """
    Analyze store financial data and generate a CFO report using AI.
    Returns CFOReport instance.
    """
    from accounting.financial_health_service import get_financial_health
    from accounting.models import CFOReport
    from core.ai_service import call_text_ai

    # Get financial data for last 90 days
    health = get_financial_health(store, days=90)

    # Build context for AI
    prompt = f"""شما یک مشاور مالی هوشمند برای یک فروشگاه آنلاین هستید.

وضعیت مالی فروشگاه در ۹۰ روز اخیر:
- درآمد: {health['revenue']:,} ریال
- هزینه‌ها: {health['total_expense']:,} ریال
- کارمزد پلتفرم: {health['commission']:,} ریال
- سود خالص: {health['net_profit']:,} ریال
- حاشیه سود: {health['profit_margin']}٪
- رشد درآمد: {health['growth']:+.1f}٪

محصولات پرفروش: {[p['product_name'] for p in health['top_products'][:3]]}

یک گزارش جامع به فارسی بنویس که شامل:
1. وضعیت کلی فروشگاه (2-3 جمله)
2. نقاط قوت
3. نقاط ضعف و هشدارها
4. پیشنهادات بهبود (حداقل 3 مورد)

پاسخ را در قالب JSON با فرمت زیر بده:
{{
  "summary": "خلاصه وضعیت کلی",
  "suggestions": ["پیشنهاد ۱", "پیشنهاد ۲", "پیشنهاد ۳"],
  "alerts": ["هشدار ۱ (اگر وجود داشت)"]
}}"""

    try:
        import json
        response = call_text_ai(store=store, prompt=prompt)
        data = json.loads(response)
        report = CFOReport.objects.create(
            store=store,
            content=data.get("summary", response),
            suggestions=data.get("suggestions", []),
            alerts=data.get("alerts", []),
        )
    except Exception:
        report = CFOReport.objects.create(
            store=store,
            content="تحلیل مالی در این دوره انجام نشد. لطفاً اطلاعات مالی را وارد کنید.",
            suggestions=[],
            alerts=[],
        )

    return report
