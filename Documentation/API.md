# UltraShop API Documentation

> **نسخه:** 1.0 | **به‌روز‌رسانی:** 2026-04-11

این سند مستندات HTTP API های عمومی و داشبورد پلتفرم UltraShop را پوشش می‌دهد.

---

## فهرست مطالب

1. [اطلاعات کلی](#اطلاعات-کلی)
2. [احراز هویت](#احراز-هویت)
3. [Storefront API](#storefront-api)
4. [Dashboard API](#dashboard-api)
5. [Platform Admin API](#platform-admin-api)
6. [کدهای خطا](#کدهای-خطا)

---

## اطلاعات کلی

| آیتم | مقدار |
|------|-------|
| Base URL (Dashboard) | `/dashboard/` |
| Base URL (Storefront) | `/s/<store_username>/` |
| Base URL (Platform Admin) | `/platform/` |
| فرمت پاسخ | HTML (views) یا JSON (endpoints مشخص‌شده) |
| احراز هویت | Session-based (Django Login) |
| زبان | فارسی (fa-IR) |
| ارز | ریال (IRR) — عدد صحیح |

---

## احراز هویت

### ورود
```
POST /accounts/login/
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `email` | string | ایمیل کاربر |
| `password` | string | رمز عبور |

**پاسخ موفق:** Redirect به داشبورد

### خروج
```
POST /accounts/logout/
```
**پاسخ موفق:** Redirect به صفحه ورود

---

## Storefront API

Base URL: `/s/<store_username>/`

### Chat API (C-06)

#### ارسال پیام به دستیار هوشمند
```
POST /s/<store_username>/chat/
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "آیا محصول X موجود است؟"
}
```

**پاسخ موفق (200):**
```json
{
  "reply": "بله، محصول X موجود است و قیمت آن ۵۰,۰۰۰ ریال است."
}
```

**خطاها:**
| کد | توضیح |
|----|-------|
| `400` | `{"error": "پیام خالی است."}` |
| `429` | `{"error": "سقف پیام‌های این گفتگو به پایان رسید."}` — بیشتر از ۲۰ پیام |

**نکته:** درخواست باید از مرورگر با session فعال ارسال شود. CSRF Token در header `X-CSRFToken` لازم است.

---

### Cart API

#### مشاهده سبد خرید
```
GET /s/<store_username>/cart/
```
**پاسخ:** HTML

#### افزودن به سبد
```
POST /s/<store_username>/cart/add/
Content-Type: application/x-www-form-urlencoded
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `variant_id` | int | شناسه تنوع محصول |
| `quantity` | int | تعداد (پیش‌فرض: 1) |

**پاسخ موفق:** Redirect به سبد خرید

#### حذف از سبد
```
POST /s/<store_username>/cart/remove/
Content-Type: application/x-www-form-urlencoded
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `variant_id` | int | شناسه تنوع محصول |

#### بازیابی سبد رهاشده
```
GET /s/<store_username>/cart/recover/<token>/
```
| پارامتر | نوع | توضیح |
|---------|-----|-------|
| `token` | UUID | توکن بازیابی ارسال‌شده از طریق SMS/Email |

---

### Product Search API

```
GET /s/<store_username>/search/?q=<query>
```
| پارامتر | نوع | توضیح |
|---------|-----|-------|
| `q` | string | عبارت جستجو |

**پاسخ:** HTML با لیست محصولات

---

### Checkout API

```
GET  /s/<store_username>/checkout/    — نمایش فرم
POST /s/<store_username>/checkout/    — ثبت سفارش
```

**فیلدهای POST:**
| فیلد | نوع | توضیح |
|------|-----|-------|
| `name` | string | نام گیرنده |
| `phone` | string | شماره موبایل |
| `address` | string | آدرس کامل |
| `city` | string | شهر |
| `province` | string | استان |
| `postal_code` | string | کد پستی |
| `email` | string (optional) | ایمیل |
| `discount_code` | string (optional) | کد تخفیف |
| `payment_method` | string | روش پرداخت (`cod` یا gateway) |

**پاسخ موفق:** Redirect به `/s/<store>/order/<id>/confirm/`

---

## Dashboard API

Base URL: `/dashboard/`
**احراز هویت الزامی:** Login + store selection

### Order Status Update

```
POST /dashboard/orders/<pk>/
Content-Type: application/x-www-form-urlencoded
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `new_status` | string | وضعیت جدید (`paid`, `packed`, `shipped`, `delivered`, `cancelled`) |
| `note` | string (optional) | یادداشت تغییر وضعیت |

**پاسخ موفق:** Redirect به صفحه جزئیات سفارش

**انتقال‌های مجاز:**
```
pending  → paid | cancelled
paid     → packed | cancelled
packed   → shipped
shipped  → delivered
```

---

### Smart Routing (SO-52)

#### نمایش پلن مسیریابی
```
GET /dashboard/orders/<pk>/smart-route/
```

#### تأیید و رزرو موجودی
```
POST /dashboard/orders/<pk>/smart-route/
Content-Type: application/x-www-form-urlencoded
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `confirm` | string `"1"` | تأیید پلن مسیریابی |

**پاسخ موفق:** Redirect به صفحه جزئیات سفارش

---

### CFO Agent (SO-36)

```
POST /dashboard/cfo-agent/
Content-Type: application/x-www-form-urlencoded
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `action` | `"generate"` | تولید گزارش جدید |

**رفتار:** تولید گزارش AI از داده‌های ۹۰ روز اخیر + ارسال ایمیل هشدار به صاحب فروشگاه (اگر هشدار وجود داشت)

---

### AI Vision — Product from Image (SO-16)

```
POST /dashboard/products/from-image/
Content-Type: multipart/form-data
```
| فیلد | نوع | توضیح |
|------|-----|-------|
| `image` | file | تصویر محصول (JPG/PNG/WebP، حداکثر 10MB) |

**پاسخ موفق:** Redirect به فرم ایجاد محصول با prefill داده‌های استخراج‌شده

---

### CRO Optimizer (SO-47)

```
POST /dashboard/cro-optimizer/
Content-Type: application/x-www-form-urlencoded
```
| action | توضیح |
|--------|-------|
| `generate` | تولید پیشنهادات بهینه‌سازی CRO با AI |
| `accept` | قبول یک پیشنهاد (`suggestion_id` لازم) |
| `dismiss` | رد یک پیشنهاد (`suggestion_id` لازم) |

---

### Content Calendar Export (SO-18)

#### دانلود CSV
```
GET /dashboard/content-calendar/export/?month=YYYY-MM
```
**پاسخ:** فایل CSV با encoding `utf-8-sig`

#### نسخه قابل چاپ / PDF
```
GET /dashboard/content-calendar/print/?month=YYYY-MM
```
**پاسخ:** HTML بهینه‌شده برای چاپ (با `@media print`)
**نکته:** برای ذخیره PDF از کاربر انتظار می‌رود از «Print → Save as PDF» مرورگر استفاده کند.

---

### Integration Test (فاز ۴)

```
POST /dashboard/integrations/<integration_id>/test/
```
**مقادیر مجاز integration_id:** `zarinpal`, `post_iran`, `moadian`

**پاسخ JSON:**
```json
{
  "success": true,
  "message": "اتصال موفق"
}
```

---

### Moadian — Submit Invoice

```
POST /dashboard/orders/<pk>/submit-invoice/
```
**پاسخ JSON:**
```json
{
  "success": true,
  "fiscal_id": "STUB-FISCAL-xxx"
}
```

---

### Track Shipment

```
GET /dashboard/orders/<pk>/track/
```
**پاسخ JSON:**
```json
{
  "success": true,
  "tracking": {
    "status": "in_transit",
    "location": "تهران"
  }
}
```

---

## Platform Admin API

Base URL: `/platform/`
**احراز هویت الزامی:** PlatformAdmin group

### AI Settings Test

```
POST /platform/ai-settings/test/
```
**پاسخ JSON:**
```json
{
  "success": true,
  "message": "اتصال به OpenAI برقرار است"
}
```

---

## کدهای خطا

| کد | معنا | کاربرد |
|----|------|---------|
| `200` | OK | عملیات موفق |
| `302` | Redirect | پس از عملیات POST (PRG pattern) |
| `400` | Bad Request | ورودی نامعتبر |
| `403` | Forbidden | عدم دسترسی به منبع |
| `404` | Not Found | منبع یافت نشد |
| `429` | Too Many Requests | محدودیت نرخ (مثلاً چت: ۲۰ پیام، AI: نرخ روزانه) |
| `500` | Server Error | خطای سرور |

---

## نکات امنیتی

- تمام درخواست‌های POST باید شامل **CSRF Token** باشند
- Chat API محدودیت ۲۰ پیام per session دارد
- AI API محدودیت روزانه per store دارد (`PlatformSettings.ai_rate_limit`)
- Session timeout: استاندارد Django (2 هفته)
- اطلاعات حساس (API key‌ها) رمزنگاری‌شده ذخیره می‌شوند
