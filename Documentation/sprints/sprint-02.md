# Sprint 2 — سیستم طراحی و تم‌ اینجین

**هدف:** پیاده‌سازی معماری توکن‌محور Design System، تم پریست‌ها، و لایه شخصی‌سازی برند. این اسپرینت پایه ویژوال پلتفرم را می‌سازد.  
**پیش‌نیاز:** Sprint 1 (PA-14 به پلتفرم ادمین نیاز دارد)  
**خروجی:** سیستم توکن، ۴ تم پریست، شخصی‌سازی برند پیشرفته، CSS سفارشی

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### SO-45: شخصی‌سازی توکن‌های طراحی و Brand Override
- **چرا اول:** بنیان کل Design System — بدون توکن‌ها هیچ تمی کار نمی‌کند
- **کارها:**
  - [x] تعریف توکن‌های سطح ۱ (Global): color scale, typography, spacing, radius, shadow, motion
  - [x] تعریف توکن‌های سطح ۲ (Semantic): button-bg, card-bg, text-heading, cta-color
  - [x] تعریف توکن‌های سطح ۳ (Component): btn-primary-bg, input-border-focus, badge-success-bg
  - [x] کامپایل توکن‌ها به CSS variables
  - [x] تزریق per-store در runtime (SSR compatible)
  - [x] کش per-domain (کش per-store با کلید store + theme.version؛ timeout ۵ دقیقه)
  - [x] مدل `StoreTheme` — آپدیت با فیلدهای: primary_color, secondary_color, accent_color, heading_font, body_font, radius_scale, shadow_level
  - [x] فرم شخصی‌سازی تم در داشبورد فروشگاه (color picker با validation کنتراست WCAG AA)
  - [x] تولید خودکار scale رنگ (50-900) از رنگ اصلی
  - [x] هشدار کنتراست ناکافی

#### SO-44: انتخاب و شخصی‌سازی تم پریست
- **وابستگی:** SO-45 (توکن‌ها باید آماده باشند)
- **کارها:**
  - [x] تعریف ۴ پریست: Minimal, Bold Commerce, Elegant, Creator
  - [x] هر پریست: typography hierarchy, spacing rhythm, radius profile, shadow intensity, animation, component defaults (در tokens پریست + seed)
  - [x] صفحه انتخاب تم با پیش‌نمایش (thumbnail یا رنگ primary از tokens + نمایش radius/shadow/spacing)
  - [x] اعمال فوری پریست (بدون از دست رفتن داده)
  - [x] ساختار `ThemePreset + BrandOverride + LayoutConfiguration + OptionalCustomCSS` (ThemePreset.tokens + StoreTheme override + custom_css)

---

### 🟠 اولویت بالا (P1)

#### SO-48: اعمال CSS سفارشی
- **وابستگی:** SO-45 (توکن‌ها باید آماده باشند)
- **کارها:**
  - [x] فیلد `custom_css` در StoreTheme
  - [x] فرم ویرایش CSS در داشبورد (textarea یا code editor ساده)
  - [x] Sanitization: حذف inline JS, محدودیت @import از URL خارجی
  - [x] سازگاری با CSP (CSPMiddleware با style-src 'self' 'unsafe-inline'؛ قابل خاموش با CSP_ENABLED=False)
  - [x] اعمال بعد از CSS تم (override capability)
  - [x] بررسی حجم (باقی ماندن در بودجه < 50kb gzipped) — محدودیت ۵۰ کیلوبایت در sanitizer + نمایش در فرم
  - [x] هشدار: «CSS نادرست ممکن است ظاهر فروشگاه را خراب کند»

#### PA-14: مدیریت Design System و حاکمیت تم
- **کارها:**
  - [x] لیست تم پریست‌ها با شماره نسخه در پنل ادمین
  - [x] CRUD پریست (افزودن، ویرایش، منسوخ کردن)
  - [x] منسوخ‌سازی: هشدار به فروشگاه‌های استفاده‌کننده + مسیر مهاجرت (تأیید با تعداد فروشگاه‌ها + پیام پس از منسوخ‌سازی)
  - [x] نمایش و ویرایش توکن‌های سطح پلتفرم (فرم ویرایش پریست با tokens به‌صورت JSON)
  - [ ] سیاست breaking change: هیچ توکنی بدون fallback حذف نشود
  - [ ] مانیتور بودجه عملکرد CSS
  - [ ] ولیدیشن دسترسی‌پذیری (WCAG 2.1 AA)

---

## مسائل فنی کلیدی

- **Token Delivery:** توکن‌ها به CSS variables کامپایل شوند → inject per-store → SSR compatible → cached per domain
- **Tenant Isolation:** هر فروشگاه CSS variable namespace مستقل دارد → بدون نشت استایل بین فروشگاه‌ها
- **Performance:** CSS bundle per store < 50kb gzipped → no blocking font load → critical CSS for above-the-fold
- **RTL:** پشتیبانی Persian-first → متغیر فونت → fallback stack

---

## تخمین حجم کار

| استوری | سایز | نکته |
|--------|------|------|
| SO-45 | XL | هسته Design System — توکن‌ها + compile + inject + فرم |
| SO-44 | L | ۴ پریست + preview + apply logic |
| SO-48 | M | sanitize + inject + budget check |
| PA-14 | L | CRUD + versioning + validation |

**مجموع:** ~4 استوری | تخمین: XL×1, L×2, M×1
