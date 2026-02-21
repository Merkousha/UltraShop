# Sprint 9 — هوش موجودی و پولیش نهایی

**هدف:** پیاده‌سازی پیش‌بینی موجودی (Inventory Forecast) و رفع باگ‌ها و بهبودهای نهایی.  
**پیش‌نیاز:** Sprint 4 (SO-50~SO-52 — Multi-Warehouse), Sprint 5 (PA-13 — AI)  
**خروجی:** سیستم پیش‌بینی موجودی + polish

---

## استوری‌ها

### 🟡 اولویت عادی (P2)

#### SO-53: پیش‌بینی موجودی و پیشنهاد بازسازی استاک
- **وابستگی:** PA-13 (AI), SO-50~SO-52 (warehouse + stock data)
- **کارها:**
  - [ ] سرویس `InventoryForecaster`
  - [ ] ورودی: تاریخچه فروش per variant (۶۰-۹۰ روز اخیر), موجودی فعلی per warehouse; lead time تأمین‌کننده (اگر موجود)
  - [ ] الگوریتم:
    - محاسبه میانگین فروش روزانه per variant
    - تخمین روزهای باقی‌مانده تا اتمام موجودی
    - پیشنهاد مقدار سفارش مجدد
  - [ ] خروجی: جدول با ستون‌های:
    - variant name
    - warehouse
    - current stock
    - avg daily sales
    - days until stockout (estimated)
    - suggested reorder quantity
    - urgency (🔴 بحرانی / 🟡 هشدار / 🟢 خوب)
  - [ ] صفحه «پیش‌بینی موجودی» در بخش انبارداری داشبورد
  - [ ] فیلتر: by warehouse, by urgency
  - [ ] مرتب‌سازی: by days until stockout (ascending)
  - [ ] Alert: هشدار خودکار وقتی variant خاصی < ۷ روز موجودی دارد
  - [ ] نوتیفیکیشن ایمیل هفتگی خلاصه وضعیت موجودی
  - [ ] AI Enhancement (اختیاری): استفاده از AI برای تحلیل ترند + تأثیر مناسبت‌ها

---

## تسک‌های Polish و بهبود

علاوه بر SO-53، این اسپرینت شامل بهبودهای عمومی است:

### بهبود عملکرد
- [ ] بررسی و بهینه‌سازی query‌های سنگین (خصوصاً aggregation مالی و موجودی)
- [ ] افزودن index‌های مناسب
- [ ] Cache layer برای داشبوردها

### بهبود UX
- [ ] یکپارچه‌سازی پیام‌های خطا و موفقیت
- [ ] بهبود responsive design برای موبایل
- [ ] بهبود RTL edge case‌ها

### تست و مستندات
- [ ] نوشتن تست‌های integration برای فلوهای اصلی
- [ ] بروزرسانی مستندات API
- [ ] بروزرسانی README پروژه

---

## ملاحظات فنی

- **Forecast Algorithm:** فعلاً simple moving average — در آینده قابل ارتقا به ML model
- **Lead Time:** فعلاً manual input (فیلد optional در Warehouse یا Variant) — در آینده auto-learn
- **Notification:** از سیستم email موجود (C-23) استفاده شود
- **Cron Job:** تحلیل هفتگی می‌تواند با Celery periodic task یا Django management command + cron اجرا شود

---

## تخمین حجم کار

| تسک | سایز | نکته |
|-----|------|------|
| SO-53 | L | forecast service + UI + alerts |
| polish عملکرد | M | query optimization + caching |
| polish UX | M | responsive + RTL + messages |
| تست و مستندات | M | integration tests + docs |

**مجموع:** 1 استوری + بهبودها | تخمین: L×1, M×3
