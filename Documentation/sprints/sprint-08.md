# Sprint 8 — عوامل هوشمند AI (AI Agents)

**هدف:** پیاده‌سازی AI Agent‌ها: CFO Agent، Customer Support Agent، CRO Optimizer، و Content Calendar.  
**پیش‌نیاز:** Sprint 5 (PA-13), Sprint 7 (SO-34, SO-35 — برای CFO Agent), Sprint 2 (SO-44, SO-45 — برای CRO)  
**خروجی:** ۴ قابلیت Agentic AI — CFO, Support, CRO, Content Calendar

---

## استوری‌ها

### 🟠 اولویت بالا (P1)

#### SO-36: عامل هوشمند CFO (AI CFO Agent)
- **وابستگی:** PA-13, SO-34, SO-35 (financial data), SO-30~SO-33 (accounting)
- **کارها:**
  - [ ] سرویس `CFOAgent` — تحلیل دوره‌ای داده‌های مالی فروشگاه
  - [ ] ورودی: فروش، هزینه‌ها، حاشیه سود، ترند، موجودی
  - [ ] خروجی AI:
    - گزارش وضعیت کلی فروشگاه (خلاصه متنی)
    - پیشنهادات بهبود (تنظیم قیمت، کاهش هزینه، تمرکز بر محصول خاص)
    - هشدارهای مهم (cash flow warning, margin alert)
  - [ ] صفحه «مشاور مالی AI» در داشبورد حسابداری
  - [ ] دکمه «تحلیل جدید» (manual trigger)
  - [ ] ذخیره تاریخچه گزارشات (مدل `CFOReport`: store, content, generated_at)
  - [ ] نوتیفیکیشن: ارسال هشدار مهم به ایمیل صاحب فروشگاه

#### C-06: عامل پشتیبانی مشتری (AI Support Agent)
- **وابستگی:** PA-13
- **کارها:**
  - [ ] ویجت چت در storefront (floating button + chat window)
  - [ ] ورودی مشتری: سؤالات متنی درباره محصولات، سفارشات، ارسال
  - [ ] AI Context: اطلاعات فروشگاه + FAQ + محصولات + وضعیت سفارش مشتری (اگر لاگین باشد)
  - [ ] پاسخ AI: متن فارسی + لینک به صفحات مرتبط
  - [ ] Handoff: اگر AI نتوانست پاسخ دهد → پیشنهاد «تماس با فروشگاه» (ایمیل/تلفن)
  - [ ] ذخیره تاریخچه مکالمات (مدل `ChatSession`, `ChatMessage`)
  - [ ] مشتری لاگین‌نشده هم می‌تواند چت کند (session-based)
  - [ ] Rate limit: حداکثر ۲۰ پیام per session
  - [ ] صاحب فروشگاه: مشاهده مکالمات در داشبورد (read-only)

---

### 🟡 اولویت عادی (P2)

#### SO-47: پیشنهادات بهینه‌سازی نرخ تبدیل (AI CRO)
- **وابستگی:** PA-13, SO-44~SO-46 (Design System + blocks)
- **کارها:**
  - [ ] سرویس `CROAnalyzer` — تحلیل ساختار صفحات فروشگاه
  - [ ] ورودی: layout configuration + theme + تعداد محصولات + آمار ساده (pageview اگر موجود باشد)
  - [ ] خروجی AI:
    - پیشنهادات بهبود (مثلاً: «CTA دکمه خرید را بالاتر قرار دهید»، «دسته‌بندی محصولات نامناسب»)
    - Score تخمینی تأثیر هر پیشنهاد (Low/Medium/High)
  - [ ] صفحه «پیشنهادات CRO» در داشبورد
  - [ ] هر پیشنهاد: Accept (اعمال خودکار اگر ممکن) / Dismiss / Later
  - [ ] حداکثر ۱ تحلیل در هفته (rate limit)

#### SO-18: تقویم محتوایی AI (Content Calendar)
- **وابستگی:** PA-13
- **کارها:**
  - [ ] صفحه «تقویم محتوا» در داشبورد
  - [ ] ورودی AI: نوع کسب‌وکار + محصولات فعال + مناسبت‌های ایرانی (نوروز، یلدا، ...)
  - [ ] خروجی AI: تقویم ۳۰ روزه با:
    - پیشنهاد موضوع (post idea)
    - پیشنهاد کپشن
    - پیشنهاد هشتگ
    - زمان انتشار پیشنهادی
  - [ ] نمایش calendar view (grid ماهانه)
  - [ ] ویرایش هر آیتم توسط کاربر
  - [ ] Export: دانلود تقویم به PDF یا CSV
  - [ ] بازتولید: تولید مجدد تقویم ماه بعد

---

## ملاحظات فنی

- **Agent Architecture:** فعلاً Direct API calls — در آینده مهاجرت به LangGraph/CrewAI
- **Chat Widget:** vanilla JS widget → inject در storefront → websocket نه لازم (polling یا SSE کافی)
- **CFO Prompt:** context window باید شامل آخرین ۳ ماه داده مالی باشد — chunk اگر زیاد شد
- **CRO:** فعلاً بدون A/B testing — فقط پیشنهاد (A/B testing در فازهای آینده)
- **Security:** ChatSession نباید به اطلاعات حساس مالی فروشگاه دسترسی داشته باشد — فقط product + order status

---

## تخمین حجم کار

| استوری | سایز | نکته |
|--------|------|------|
| SO-36 | L | analysis service + report model + notification |
| C-06 | XL | chat widget + AI context + history + handoff |
| SO-47 | L | analyzer + suggestions UI + accept/dismiss |
| SO-18 | L | calendar + Iranian events + export |

**مجموع:** ~4 استوری | تخمین: XL×1, L×3

> ⚠️ این اسپرینت سنگین‌ترین اسپرینت از نظر AI integration است. در صورت نیاز، SO-47 و SO-18 به اسپرینت بعد موکول شوند.
