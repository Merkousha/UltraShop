# Sprint 5 — زیرساخت AI و اولین قابلیت‌های محتوایی

**هدف:** راه‌اندازی زیرساخت سرویس‌های AI (تنظیمات، API key ها، rate limit) و پیاده‌سازی دو قابلیت محتوایی: Vision-to-Listing و SEO Automator.  
**پیش‌نیاز:** Sprint 1 (PA-15 برای زیرساخت ارتباطات)  
**خروجی:** AI service config، Vision-to-Listing، Auto SEO  

**وضعیت:** ✅ انجام شد

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### PA-13: تنظیمات سرویس‌های AI ✅
- **چرا اول:** همه قابلیت‌های AI به این تنظیمات وابسته هستند
- **کارها:**
  - [x] فیلدها در `PlatformSettings`: openai_api_key_encrypted, anthropic_api_key_encrypted, vision_model, text_model, image_gen_model, ai_enabled, rate_limit_per_store_daily؛ مدل `AIDailyUsage` (store, date, usage_count) برای rate limit
  - [x] فرم تنظیمات در پنل ادمین: `/platform/settings/ai/`
  - [x] رمزنگاری API keys با `core.encryption.encrypt_value`
  - [x] دکمه «تست اتصال» برای OpenAI (فراخوانی کوچک chat)
  - [x] ثبت تغییرات در audit log (action: ai_settings_updated)
  - [x] سرویس `core.ai_service`: vision_extract_product, text_generate_seo، _get_client، _check_and_consume_rate_limit، retry و AIError با user_message

---

### 🟠 اولویت بالا (P1)

#### SO-16: ایجاد محصول از عکس (Vision-to-Listing) ✅
- **وابستگی:** PA-13
- **کارها:**
  - [x] دکمه «ساخت از عکس» در لیست محصولات → `/dashboard/products/add-from-image/`
  - [x] آپلود تصویر (file picker)، حداکثر ۱۰ مگابایت
  - [x] فراخوانی Vision API (مدل از تنظیمات) — استخراج name, description, category_suggestion, attributes (JSON)
  - [x] Pre-fill فرم افزودن محصول با session؛ تطبیق دسته‌بندی با نام پیشنهادی (name__icontains)
  - [x] کاربر می‌تواند همه فیلدها را ویرایش کند
  - [x] شمارشگر اعتبار AI در لیست محصولات و صفحه «ساخت از عکس»
  - [x] Error handling: تصویر نامعتبر، خطای API، rate limit (AIError.user_message)
  - [ ] *(اختیاری)* Progress indicator (loading state) — فرم ساده با دکمه submit

#### SO-17: تولید خودکار محتوای SEO ✅
- **وابستگی:** PA-13
- **کارها:**
  - [x] دکمه «تولید SEO با AI» در فرم ویرایش محصول (AJAX به `/products/<id>/generate-seo/`)
  - [x] ورودی AI: نام + توضیحات + دسته‌بندی + زبان fa-IR
  - [x] خروجی AI: meta_title, meta_description, focus_keywords, og_description؛ فیلدهای focus_keywords و og_description روی Product اضافه شد
  - [x] Pre-fill فیلدهای SEO در فرم (قابل ویرایش)
  - [x] پشتیبانی فارسی (lang=fa-IR)
  - [x] Bulk SEO: گزینه «تولید SEO با AI» در عملیات گروهی؛ اعمال روی انتخاب‌شده‌ها با بررسی rate limit
  - [x] شمارشگر اعتبار در فرم و لیست

---

## ملاحظات فنی

- **Architecture:** سرویس AI به صورت sync (در Django view) پیاده شود — در آینده به FastAPI microservice منتقل می‌شود
- **Security:** API keys باید encrypted در DB ذخیره شوند (django-encrypted-model-fields یا مشابه)
- **Rate Limiting:** per-store daily counter — ذخیره در Redis یا DB field
- **Prompt Engineering:** پرامپت‌ها باید configurable باشند (نه hard-coded) — ذخیره در DB یا settings
- **Error Handling:** graceful degradation — اگر AI در دسترس نیست، کاربر هنوز می‌تواند محصول را دستی بسازد
- **Cost:** هر فراخوانی Vision حدود $0.01-0.05 — tracking هزینه per store

---

## تخمین حجم کار

| استوری | سایز | نکته |
|--------|------|------|
| PA-13 | L | encrypted config + wrapper service + test |
| SO-16 | XL | vision API + form integration + UX |
| SO-17 | L | text API + SEO fields + bulk |

**مجموع:** ~3 استوری | تخمین: XL×1, L×2

---

## پیاده‌سازی (خلاصه)

- **مدل‌ها:** `core/models.py` — فیلدهای AI در PlatformSettings؛ `AIDailyUsage`. `catalog/models.py` — Product.focus_keywords, Product.og_description
- **مایگریشن‌ها:** core/0006_ai_config_and_usage، catalog/0005_product_seo_fields
- **سرویس:** `core/ai_service.py` — vision_extract_product, text_generate_seo, get_ai_usage_today, is_ai_available_for_store؛ وابستگی openai
- **پنل ادمین:** `platform_admin/views.py` — AISettingsView, TestAIView؛ `/platform/settings/ai/`
- **داشبورد:** ProductFromImageView (آپلود عکس → Vision → redirect به product-create با session)؛ ProductGenerateSEOView (POST JSON)؛ فرم محصول با فیلدهای SEO و دکمه تولید؛ bulk action generate_seo
- **وابستگی:** `openai>=1.0.0` در requirements.txt
