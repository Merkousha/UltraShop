# Sprint 4 — چند انباری و مسیریابی هوشمند

**هدف:** پیاده‌سازی سیستم Multi-Warehouse: مدیریت چند انبار، تخصیص موجودی، مسیریابی هوشمند سفارشات.  
**پیش‌نیاز:** Sprint 1 (PA-20, PA-22, PA-23 — زیرساخت ارسال باید کامل باشد)  
**خروجی:** مدل انبار، موجودی per-warehouse، Smart Routing، داشبورد استاف

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### SO-50: ایجاد و مدیریت چند انبار
- **چرا اول:** بنیان کل سیستم Multi-Warehouse
- **کارها:**
  - [ ] مدل `Warehouse` (store FK, name, address, city, province, postal_code, phone, is_active, priority)
  - [ ] CRUD انبار در داشبورد فروشگاه
  - [ ] انبار پیش‌فرض اولین فروشگاه (مهاجرت از ساختار فعلی بدون انبار)
  - [ ] Migration: تبدیل `ProductVariant.stock` فعلی به `WarehouseStock`
  - [ ] حداکثر تعداد انبار per plan (free: 1, premium: 5+)

#### SO-51: تخصیص موجودی به انبارها
- **وابستگی:** SO-50
- **کارها:**
  - [ ] مدل `WarehouseStock` (warehouse FK, variant FK, quantity, reserved, last_restocked_at)
  - [ ] صفحه مدیریت موجودی per-warehouse
  - [ ] نمایش خلاصه موجودی: total across warehouses
  - [ ] Transfer stock: انتقال موجودی بین انبارها با ثبت log
  - [ ] حفظ backward compatibility: `variant.stock` = sum(warehouse_stocks)

#### SS-13: مدیریت موجودی انبار توسط استاف
- **وابستگی:** SO-50, SO-51
- **کارها:**
  - [ ] اختصاص استاف به انبار(ها) — فیلد ManyToMany در StoreStaff
  - [ ] عدم دسترسی استاف به انبارهایی که عضوشان نیست
  - [ ] ویوی موجودی فقط برای انبارهای مجاز
  - [ ] ثبت تغییرات موجودی + actor log

---

### 🟠 اولویت بالا (P1)

#### SO-52: مسیریابی هوشمند ارسال سفارش
- **وابستگی:** SO-50, SO-51 (موجودی per-warehouse باید آماده باشد)
- **کارها:**
  - [ ] سرویس `SmartRoutingService`
  - [ ] الگوریتم: نزدیک‌ترین انبار به آدرس مشتری (بر اساس شهر/استان)
  - [ ] فالبک: اگر انبار نزدیک موجودی ندارد → انبار بعدی
  - [ ] Split shipment: اگر هیچ انباری همه آیتم‌ها را ندارد → تقسیم سفارش
  - [ ] نمایش پیشنهاد مسیریابی به صاحب فروشگاه قبل از تأیید ارسال
  - [ ] Override دستی: صاحب فروشگاه می‌تواند انبار دیگری انتخاب کند
  - [ ] تنظیمات: auto-route vs manual-approve در preferences

---

## ملاحظات فنی

- **Migration Path:** موجودی فعلی (ProductVariant.stock) باید به اولین WarehouseStock انتقال یابد — data migration + backward compat
- **Performance:** aggregation موجودی (total stock = SUM) باید بهینه باشد — ممکن است denormalized field نیاز باشد
- **Routing:** فعلاً proximity بر اساس province matching — در آینده با Geocoding API قابل ارتقا
- **Concurrency:** رزرو موجودی (`reserved` field) باید atomic باشد (F expression یا select_for_update)

---

## تخمین حجم کار

| استوری | سایز | نکته |
|--------|------|------|
| SO-50 | L | مدل + CRUD + migration |
| SO-51 | L | WarehouseStock + transfer + compat |
| SS-13 | M | access control + warehouse assignment |
| SO-52 | XL | routing algorithm + split shipment + UI |

**مجموع:** ~4 استوری | تخمین: XL×1, L×2, M×1
