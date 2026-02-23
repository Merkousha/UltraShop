# Sprint 3 — ویرایشگر بلوکی صفحه (Drag & Drop Page Editor)

**هدف:** پیاده‌سازی سیستم بلوک‌های صفحه و ویرایشگر Drag & Drop برای چیدمان storefront. این اسپرینت امکان ساخت صفحه‌ بدون کد را فراهم می‌کند.  
**پیش‌نیاز:** Sprint 2 (Design System باید آماده باشد — بلوک‌ها از توکن‌ها استفاده می‌کنند)  
**خروجی:** ویرایشگر بلوکی، مدل LayoutConfiguration، preview و rollback  

**وضعیت:** ✅ انجام شد (فازهای A، B، C پیاده‌سازی شده‌اند)

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### SO-46: ویرایشگر بلوکی Drag & Drop
- **بزرگ‌ترین استوری این اسپرینت** — ممکن است به sub-task تقسیم شود
- **کارها:**

**فاز A — مدل و بلوک‌ها:** ✅
  - [x] مدل `LayoutConfiguration` (store, page_type, block_order JSON, block_settings JSON, block_enabled, version) + `LayoutConfigurationSnapshot` برای rollback
  - [x] تعریف بلوک‌های اتمیک در `core/blocks.py` و قالب‌ها در `templates/storefront/blocks/`:
    - [x] Hero (تصویر + عنوان + CTA)
    - [x] Product Grid (تعداد ستون + تعداد محصول + فیلتر)
    - [x] Category Grid (لیست دسته‌بندی‌ها)
    - [x] Banner (تصویر + لینک)
    - [x] Testimonials (نقل‌قول‌های مشتری)
    - [x] FAQ (سؤالات متداول آکاردئونی)
    - [x] Newsletter Signup (فرم عضویت خبرنامه)
    - [x] Custom Section (HTML/text سفارشی؛ با sanitize برای امنیت)
  - [x] هر بلوک: قالب فارسی/RTL؛ token binding از طریق CSS variables فروشگاه
  - [ ] *(اختیاری)* responsive/animation rules و فیلدهای قابل تنظیم پر شده در editor

**فاز B — ویرایشگر:** ✅
  - [x] صفحه ویرایشگر در داشبورد (`/dashboard/pages/edit/`) با لینک «ویرایشگر صفحه» در سایدبار
  - [x] Drag & drop برای تغییر ترتیب بلوک‌ها (SortableJS)
  - [x] فعال/غیرفعال هر بلوک (toggle) — ذخیره درست برای چک‌باکس‌های unchecked
  - [ ] *(اختیاری)* تنظیمات هر بلوک در sidebar (فیلدهای setting_* در مدل آماده است)
  - [x] پشتیبانی صفحه home؛ بقیه صفحات (category, product, custom) برای بعد

**فاز C — Preview و Versioning:** ✅
  - [x] دکمه «پیش‌نمایش» — لینک به storefront home برای دیدن تغییرات پس از انتشار
  - [x] دکمه «انتشار» — ذخیره snapshot و افزایش version؛ اعمال روی storefront
  - [x] Version tracking و snapshots در `LayoutConfigurationSnapshot`
  - [x] Rollback: بازگشت به نسخه قبلی از dropdown و دکمه «بازگشت به این نسخه»
  - [ ] *(اختیاری)* Mobile preview در عرض موبایل در همان ویرایشگر

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

---

## پیاده‌سازی (خلاصه)

- **مدل:** `core/models.py` — `LayoutConfiguration`, `LayoutConfigurationSnapshot`؛ migration `core/migrations/0003_layout_configuration.py`
- **بلوک‌ها:** `core/blocks.py` (BLOCK_REGISTRY)، `core/layout_service.py` (`get_layout_blocks`)، قالب‌ها: `templates/storefront/blocks/*.html`
- **Storefront:** `storefront/views.py` (`StoreHomeView`)، `storefront/home.html` (رندر بلوک‌ها یا محتوای legacy)
- **امنیت Custom block:** `storefront/templatetags/storefront_block_filters.py` — `sanitize_block_html`
- **ویرایشگر:** `dashboard/views.py` — `PageEditorView`, `PagePublishView`, `PageRollbackView`؛ URLها: `dashboard/pages/edit/`, `pages/publish/`, `pages/rollback/`
- **قالب ویرایشگر:** `templates/dashboard/page_editor.html` (SortableJS، لیست بلوک، ذخیره / انتشار / rollback با dropdown نسخه‌ها)
- **ناوبری:** لینک «ویرایشگر صفحه» در `templates/dashboard/base.html`
