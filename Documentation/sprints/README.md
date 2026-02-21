# Sprint Planning — UltraShop Platform

## وضعیت فعلی (Implementation Status)

بر اساس بخش Implementation Progress در PRD، ویژگی‌های زیر **پیاده‌سازی شده** هستند:

### ✅ پیاده‌سازی شده

| حوزه | استوری‌ها | توضیح |
|------|-----------|-------|
| **Phase 0 — زیرساخت** | SO-01, SO-02, SO-03, SO-05 | Django project, User, Store, tenant middleware, signup/login, dashboard |
| **احراز هویت مشتری** | C-09, C-09b, C-13 | Customer + LoginOTP models, OTP service, phone+OTP views, session-scoped |
| **کاتالوگ** | SO-10, SO-11, SO-12, SO-13 | Category, Product, ProductVariant; storefront views; dashboard CRUD |
| **سبد و چک‌اوت** | C-05, C-10, C-11, C-12 | Session-based cart, checkout flow, guest checkout, place order |
| **درگاه پرداخت** | C-11 | Payment model, MockGateway, ZarinPalGateway |
| **سفارشات** | SO-20, SO-21, SO-22, SO-23, SO-24 | Order lifecycle, dashboard, cancel, refund, status timeline |
| **سفارشات مشتری** | C-20, C-21, C-22 | My orders, order detail, shipment tracking |
| **ارسال پلتفرم** | SO-22, PA-21 | Shipment model, create shipment, track, ShippingCarrier CRUD |
| **حسابداری** | SO-30, SO-31, SO-32, SO-33 | Ledger, summary, payouts, CSV export |
| **دامنه و برندینگ** | SO-40, SO-41, SO-42, SO-43 | StoreDomain, DNS instructions, basic branding |
| **کارکنان** | SO-04, SS-01–SS-05, SS-10–SS-12 | StoreStaff model, RBAC, orders/inventory access |
| **ویترین فروشگاه** | C-01, C-02, C-03 | Storefront, categories, product detail |
| **پنل ادمین پلتفرم** | PA-01, PA-02, PA-03, PA-04, PA-10 | Login, RBAC, audit log, password policy, platform settings |
| **فروشگاه‌ها (ادمین)** | PA-30, PA-31, PA-32, PA-33, PA-34 | Store list, detail, suspend, payouts, commission |
| **اعلان‌ها** | C-23 | Order confirmation email, shipping email |

### ❌ باقی‌مانده (۲۸ استوری)

این استوری‌ها در ۹ اسپرینت اولویت‌بندی شده‌اند:

| اسپرینت | تمرکز | استوری‌ها | تعداد |
|---------|--------|-----------|-------|
| **Sprint 1** | تکمیل زیرساخت پلتفرم | PA-11, PA-12, PA-15, PA-20, PA-22, PA-23, PA-35, C-04, SO-14, SO-15 | 10 |
| **Sprint 2** | سیستم طراحی و تم | SO-44, SO-45, SO-48, PA-14 | 4 |
| **Sprint 3** | ویرایشگر بلوکی صفحه | SO-46 | 1 |
| **Sprint 4** | انبارداری چندگانه | SO-50, SO-51, SO-52, SS-13 | 4 |
| **Sprint 5** | زیرساخت AI و تولید محتوا | PA-13, SO-16, SO-17 | 3 |
| **Sprint 6** | آنبوردینگ هوشمند | SO-06, SO-07 | 2 |
| **Sprint 7** | هوشمندسازی مالی | SO-34, SO-35 | 2 |
| **Sprint 8** | ایجنت‌های هوشمند | SO-36, C-06, SO-47, SO-18 | 4 |
| **Sprint 9** | پیش‌بینی موجودی | SO-53 | 1 |

---

## اصول اولویت‌بندی

1. **وابستگی‌ها اول:** زیرساخت‌هایی که سایر فیچرها به آن‌ها وابسته‌اند (پلتفرم ادمین، Design System)
2. **ارزش تجاری:** فیچرهایی که بیشترین تأثیر روی تجربه کاربر و فروش دارند
3. **ریسک فنی:** فیچرهای پیچیده‌تر زودتر شروع شوند تا زمان برای رفع مشکلات باشد
4. **AI آخر:** قابلیت‌های AI به زیرساخت‌های پایه (PA-13) وابسته‌اند و پس از تثبیت هسته اصلی

---

## نقشه وابستگی‌ها

```
Sprint 1 (زیرساخت پلتفرم)
  │
  ├── Sprint 2 (Design System) ──► Sprint 3 (Block Editor)
  │                                    │
  │                                    ▼
  │                              Sprint 6 (AI Onboarding) ◄── Sprint 5 (AI Infra)
  │                                                               │
  ├── Sprint 4 (Multi-Warehouse) ──► Sprint 9 (Inventory Forecast)│
  │                                                               │
  └── Sprint 5 (AI Infrastructure) ──► Sprint 7 (Financial AI)   │
                                         │                        │
                                         ▼                        │
                                   Sprint 8 (AI Agents) ◄────────┘
```

---

## ساختار فایل‌ها

```
sprints/
├── README.md              (این فایل — نمای کلی)
├── sprint-01.md           (تکمیل زیرساخت پلتفرم)
├── sprint-02.md           (سیستم طراحی و تم)
├── sprint-03.md           (ویرایشگر بلوکی)
├── sprint-04.md           (انبارداری چندگانه)
├── sprint-05.md           (زیرساخت AI و تولید محتوا)
├── sprint-06.md           (آنبوردینگ هوشمند)
├── sprint-07.md           (هوشمندسازی مالی)
├── sprint-08.md           (ایجنت‌های هوشمند)
└── sprint-09.md           (پیش‌بینی موجودی)
```
