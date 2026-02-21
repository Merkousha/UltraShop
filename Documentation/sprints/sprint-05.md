# Sprint 5 — زیرساخت AI و اولین قابلیت‌های محتوایی

**هدف:** راه‌اندازی زیرساخت سرویس‌های AI (تنظیمات، API key ها، rate limit) و پیاده‌سازی دو قابلیت محتوایی: Vision-to-Listing و SEO Automator.  
**پیش‌نیاز:** Sprint 1 (PA-15 برای زیرساخت ارتباطات)  
**خروجی:** AI service config، Vision-to-Listing، Auto SEO

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### PA-13: تنظیمات سرویس‌های AI
- **چرا اول:** همه قابلیت‌های AI به این تنظیمات وابسته هستند
- **کارها:**
  - [ ] مدل `AIServiceConfig` یا فیلدها در PlatformSettings:
    - `openai_api_key` (encrypted)
    - `anthropic_api_key` (encrypted)
    - `vision_model` (default: gpt-4o)
    - `text_model` (default: gpt-4o-mini)
    - `image_gen_model` (default: flux)
    - `ai_enabled` (global toggle)
    - `rate_limit_per_store_daily` (default: 50)
  - [ ] فرم تنظیمات در پنل ادمین
  - [ ] رمزنگاری API keys قبل از ذخیره
  - [ ] دکمه «تست اتصال» برای هر سرویس
  - [ ] ثبت تغییرات در audit log
  - [ ] سرویس `AIService` — wrapper برای فراخوانی مدل‌ها با error handling و retry

---

### 🟠 اولویت بالا (P1)

#### SO-16: ایجاد محصول از عکس (Vision-to-Listing)
- **وابستگی:** PA-13 (AI config باید آماده باشد)
- **کارها:**
  - [ ] دکمه «ساخت محصول از عکس» در صفحه لیست محصولات
  - [ ] آپلود تصویر (drag & drop یا file picker)
  - [ ] فراخوانی Vision API (GPT-4o) — استخراج: عنوان، توضیحات، دسته‌بندی پیشنهادی، ویژگی‌ها (رنگ، سایز، جنس)
  - [ ] Pre-fill فرم افزودن محصول با نتایج AI
  - [ ] کاربر می‌تواند همه فیلدها را قبل از ذخیره ویرایش کند
  - [ ] شمارشگر اعتبار AI (rate limit per store)
  - [ ] Error handling: تصویر نامعتبر، خطای API، rate limit exceeded
  - [ ] Progress indicator (loading state)

#### SO-17: تولید خودکار محتوای SEO
- **وابستگی:** PA-13
- **کارها:**
  - [ ] دکمه «تولید SEO» در فرم ویرایش محصول
  - [ ] ورودی AI: نام محصول + توضیحات + دسته‌بندی + زبان فروشگاه
  - [ ] خروجی AI: meta_title, meta_description, focus_keywords, og_description
  - [ ] Pre-fill فیلدهای SEO محصول (قابل ویرایش توسط کاربر)
  - [ ] پشتیبانی فارسی: تولید محتوا به fa-IR
  - [ ] Bulk SEO: اعمال روی چند محصول انتخاب‌شده (از SO-14)
  - [ ] شمارشگر اعتبار AI

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
