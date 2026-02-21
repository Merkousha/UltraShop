# Sprint 3 — ویرایشگر بلوکی صفحه (Drag & Drop Page Editor)

**هدف:** پیاده‌سازی سیستم بلوک‌های صفحه و ویرایشگر Drag & Drop برای چیدمان storefront. این اسپرینت امکان ساخت صفحه‌ بدون کد را فراهم می‌کند.  
**پیش‌نیاز:** Sprint 2 (Design System باید آماده باشد — بلوک‌ها از توکن‌ها استفاده می‌کنند)  
**خروجی:** ویرایشگر بلوکی، مدل LayoutConfiguration، preview و rollback

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### SO-46: ویرایشگر بلوکی Drag & Drop
- **بزرگ‌ترین استوری این اسپرینت** — ممکن است به sub-task تقسیم شود
- **کارها:**

**فاز A — مدل و بلوک‌ها:**
  - [ ] مدل `LayoutConfiguration` (store, page_type, block_order JSON, block_settings_json, version)
  - [ ] تعریف بلوک‌های اتمیک:
    - [ ] Hero (تصویر + عنوان + CTA)
    - [ ] Product Grid (تعداد ستون + تعداد محصول + فیلتر)
    - [ ] Category Grid (لیست دسته‌بندی‌ها)
    - [ ] Banner (تصویر + لینک)
    - [ ] Testimonials (نقل‌قول‌های مشتری)
    - [ ] FAQ (سؤالات متداول آکاردئونی)
    - [ ] Newsletter Signup (فرم عضویت خبرنامه)
    - [ ] Custom Section (HTML/text سفارشی)
  - [ ] هر بلوک: token binding, responsive rules, animation rules, configurable content fields
  - [ ] هر بلوک: قالب فارسی/RTL

**فاز B — ویرایشگر:**
  - [ ] صفحه ویرایشگر در داشبورد (`/dashboard/pages/edit/`)
  - [ ] Drag & drop برای تغییر ترتیب بلوک‌ها
  - [ ] فعال/غیرفعال هر بلوک (toggle)
  - [ ] تنظیمات هر بلوک (sidebar panel با فیلدهای قابل تنظیم)
  - [ ] پشتیبانی از صفحات: home, category, product detail, custom pages

**فاز C — Preview و Versioning:**
  - [ ] دکمه «پیش‌نمایش» — نمایش تغییرات قبل از انتشار
  - [ ] دکمه «انتشار» — ذخیره و اعمال روی storefront
  - [ ] Version tracking: هر ذخیره یک نسخه جدید ایجاد می‌کند
  - [ ] Rollback: بازگشت به نسخه قبلی layout
  - [ ] Mobile preview: نمایش responsive در عرض موبایل

---

## ملاحظات فنی

- **JS Framework:** نیاز به یک drag & drop library (مثلاً SortableJS یا @dnd-kit) — سبک و بدون وابستگی سنگین
- **Rendering:** بلوک‌ها هم در editor (JavaScript) و هم در storefront (Django template) رندر می‌شوند
- **Token Binding:** هر بلوک باید از CSS variables فروشگاه (Sprint 2) استفاده کند — نه hard-coded styles
- **Performance:** بلوک‌ها lazy-load شوند؛ تصاویر responsive با `srcset`
- **Security:** بلوک Custom Section باید sanitize شود (no inline JS)

---

## تخمین حجم کار

| تسک | سایز | نکته |
|-----|------|------|
| فاز A — مدل و بلوک‌ها | L | ۸ نوع بلوک + مدل + templates |
| فاز B — ویرایشگر | XL | Drag & drop UI + sidebar config |
| فاز C — Preview و Versioning | M | Versioning + rollback + preview |

**مجموع:** 1 استوری بزرگ (SO-46) | تخمین: XL overall

> ⚠️ این اسپرینت ممکن است بیش از دو هفته طول بکشد. در صورت نیاز، فاز C (versioning و rollback) به اسپرینت بعد موکول شود.
