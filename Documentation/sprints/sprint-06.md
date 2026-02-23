# Sprint 6 — AI Onboarding و تولید هویت برند

**هدف:** پیاده‌سازی ویزارد onboarding هوشمند با AI و تولید خودکار هویت بصری برند.  
**پیش‌نیاز:** Sprint 5 (PA-13 — AI service config)، Sprint 2 (SO-44, SO-45 — Design System)  
**خروجی:** AI onboarding wizard، AI brand identity generation  

**وضعیت:** ✅ SO-06 و SO-07 (بخش متنی) انجام شد. تولید تصویر لوگو/favicon به اسپرینت بعد موکول شد.

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### SO-06: ویزارد Onboarding هوشمند با AI ✅
- **وابستگی:** PA-13 (AI), SO-44/SO-45 (theme presets)
- **کارها:**

**مرحله ۱ — جمع‌آوری اطلاعات کسب‌وکار:** ✅
  - [x] فرم: نوع کسب‌وکار، نام برند، شعار، مخاطب هدف، سبک ترجیحی، رنگ موردعلاقه
  - [x] دکمه «ادامه و پیشنهاد با AI» و «شروع از صفر» (رفتن به انتخاب تم)

**مرحله ۲ — تحلیل AI:** ✅
  - [x] ارسال اطلاعات به AI (text model)؛ تابع `onboarding_suggest_theme` در core/ai_service
  - [x] AI Response: theme_slug (از لیست پریست‌های فعال)، primary/secondary/accent رنگ، block_order صفحه اصلی
  - [x] صفحه «دریافت پیشنهاد با AI» یا «رد کردن و انتخاب دستی»

**مرحله ۳ — تأیید و اعمال:** ✅
  - [x] نمایش پیشنهاد (تم، رنگ‌ها، چیدمان بلوک‌ها)
  - [x] دکمه «اعمال همه» — ذخیره theme preset + StoreTheme (رنگ‌ها) + LayoutConfiguration (block_order)؛ به‌روزرسانی نام فروشگاه در صورت وارد شدن
  - [x] گزینه «شروع از صفر» — redirect به theme-select

**مرحله ۴ — محصول اولیه:** ✅
  - [x] لینک به «ساخت محصول از عکس» و «افزودن محصول دستی»؛ دکمه «رفتن به داشبورد»

**فنی:** وضعیت wizard در session (`onboarding_wizard`: step, data, suggestion). لینک «راه‌اندازی با AI» در سایدبار داشبورد.

---

### 🟠 اولویت بالا (P1)

#### SO-07: تولید هویت بصری برند با AI (بخش متنی ✅؛ تصویر موکول)
- **وابستگی:** PA-13 (AI), SO-45 (design tokens)
- **کارها:**
  - [x] ورودی: نام برند، نوع کسب‌وکار، سبک، رنگ پایه
  - [x] فراخوانی Text AI: تولید tagline + brand_story (`text_generate_brand_identity`)
  - [x] صفحه «هویت برند (AI)» در داشبورد: فرم تولید، پیش‌نمایش و ویرایش، «اعمال روی فروشگاه» (Store.tagline + Store.description)
  - [x] فیلد `Store.tagline` (migration 0007_store_tagline)
  - [ ] *(موکول)* فراخوانی Vision/Image AI برای لوگو، پالت، favicon و gallery

---

## ملاحظات فنی

- **Wizard State:** progress wizard به صورت session-based یا مدل `OnboardingProgress` با مراحل و وضعیت
- **AI Prompt:** تم پیشنهادی باید از لیست تم پریست‌های موجود (SO-44) انتخاب شود — AI نمی‌تواند تم جدید اختراع کند
- **Image Generation:** فعلاً لوگو ساده (icon-style) — اگر نتیجه AI رضایت‌بخش نبود، کاربر لوگوی خودش را آپلود کند
- **Cost Control:** هر بار بازتولید هویت برند حدود $0.1-0.3 — شمارشگر اعتبار + هشدار
- **Fallback:** اگر AI خطا داد → wizard ادامه می‌یابد بدون AI → تنظیم دستی

---

## تخمین حجم کار

| استوری | سایز | نکته |
|--------|------|------|
| SO-06 | XL | 4-step wizard + AI integration + preview |
| SO-07 | XL | text + image generation + gallery UX |

**مجموع:** ~2 استوری | تخمین: XL×2

> ⚠️ این اسپرینت UX-heavy است. نیاز به طراحی wireframe قبل از شروع کد دارد.

---

## پیاده‌سازی (خلاصه)

- **SO-06:** `core/ai_service.py` — `onboarding_suggest_theme(business_type, brand_name, slogan, audience, style, favorite_color, store, preset_slugs, block_ids)`؛ خروجی theme_slug، رنگ‌ها، block_order. داشبورد: `OnboardingWizardView`، session key `onboarding_wizard`، قالب‌های `onboarding_step1.html` تا `onboarding_step4.html`؛ URL `dashboard/onboarding/`.
- **SO-07 (متنی):** `core/ai_service.py` — `text_generate_brand_identity(brand_name, business_type, style, base_color, store)`؛ `core/models.Store.tagline`؛ `BrandIdentityView`، `dashboard/brand_identity.html`، URL `dashboard/brand-identity/`.
- **ناوبری:** لینک‌های «راه‌اندازی با AI» و «هویت برند (AI)» در سایدبار داشبورد.
