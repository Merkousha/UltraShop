# Sprint 4 — چند انباری و مسیریابی هوشمند

**هدف:** پیاده‌سازی سیستم Multi-Warehouse: مدیریت چند انبار، تخصیص موجودی، مسیریابی هوشمند سفارشات.  
**پیش‌نیاز:** Sprint 1 (PA-20, PA-22, PA-23 — زیرساخت ارسال باید کامل باشد)  
**خروجی:** مدل انبار، موجودی per-warehouse، Smart Routing، داشبورد استاف  

**وضعیت:** ✅ SO-50, SO-51, SS-13 انجام شد. SO-52 (مسیریابی هوشمند) به اسپرینت بعد موکول شد.

---

## استوری‌ها

### 🔴 اولویت بحرانی (P0)

#### SO-50: ایجاد و مدیریت چند انبار ✅
- **چرا اول:** بنیان کل سیستم Multi-Warehouse
- **کارها:**
  - [x] مدل `Warehouse` (store, name, address, city, province, postal_code, phone, is_active, is_default, priority)
  - [x] CRUD انبار در داشبورد: لیست، افزودن، ویرایش؛ حداکثر ۵ انبار per store
  - [x] انبار پیش‌فرض: اولین انبار هر فروشگاه با `is_default=True`؛ data migration یک انبار «انبار پیش‌فرض» per store
  - [x] Migration: `WarehouseStock` اضافه شد؛ data migration کپی `ProductVariant.stock` به انبار پیش‌فرض
  - [x] حداکثر تعداد انبار: `MAX_WAREHOUSES_PER_STORE = 5` در `core.warehouse_service`

#### SO-51: تخصیص موجودی به انبارها ✅
- **وابستگی:** SO-50
- **کارها:**
  - [x] مدل `WarehouseStock` (warehouse, variant, quantity, reserved, last_restocked_at) در `catalog`
  - [x] صفحه مدیریت موجودی per-warehouse: `/dashboard/warehouses/<id>/inventory/`
  - [x] نمایش خلاصه: `ProductVariant.total_stock` و در فرم محصول؛ موجودی کل در انتقال
  - [x] Transfer stock: صفحه «انتقال موجودی» بین دو انبار با اعتبارسنجی موجودی
  - [x] Backward compatibility: `variant.stock` با sum(warehouse_stocks) همگام می‌شود؛ ایجاد/ویرایش محصول و bulk set_stock از `set_default_warehouse_quantity` استفاده می‌کنند

#### SS-13: مدیریت موجودی انبار توسط استاف ✅
- **وابستگی:** SO-50, SO-51
- **کارها:**
  - [x] اختصاص استاف به انبار(ها): فیلد `StoreStaff.warehouses` (ManyToMany)
  - [x] عدم دسترسی به انبارهای غیرمجاز: `get_warehouses_for_user(store, user)`؛ لیست انبارها و موجودی فقط انبارهای مجاز
  - [x] ویوی موجودی فقط برای انبارهای مجاز
  - [x] صفحه «دسترسی انبار استاف» (مالک): انتخاب انبارهای هر استاف؛ خالی = همه انبارها
  - [ ] *(اختیاری)* ثبت تغییرات موجودی + actor log (لاگ جداگانه)

---

### 🟠 اولویت بالا (P1)

#### SO-52: مسیریابی هوشمند ارسال سفارش (موکول به اسپرینت بعد)
- **وابستگی:** SO-50, SO-51 (موجودی per-warehouse آماده است)
- **کارها:**
  - [ ] سرویس `SmartRoutingService`
  - [ ] الگوریتم: نزدیک‌ترین انبار به آدرس مشتری (شهر/استان)
  - [ ] فالبک و Split shipment
  - [ ] نمایش پیشنهاد مسیریابی و Override دستی
  - [ ] تنظیمات auto-route vs manual-approve

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

---

## پیاده‌سازی (خلاصه)

- **مدل‌ها:** `core/models.py` — `Warehouse`؛ `StoreStaff.warehouses` (M2M). `catalog/models.py` — `WarehouseStock`؛ `ProductVariant.total_stock` / `total_reserved`
- **سرویس:** `core/warehouse_service.py` — `get_default_warehouse`, `set_default_warehouse_quantity`, `get_warehouses_for_user`, `MAX_WAREHOUSES_PER_STORE`
- **مایگریشن‌ها:** `core/migrations/0004_warehouse_and_staff_warehouses`, `0005_default_warehouse_per_store`؛ `catalog/migrations/0003_warehouse_stock`, `0004_populate_warehouse_stock_from_variant_stock`
- **داشبورد:** انبارها (`/dashboard/warehouses/`): لیست، افزودن، ویرایش؛ موجودی انبار (`/warehouses/<id>/inventory/`)؛ انتقال موجودی (`/warehouses/transfer/`)؛ دسترسی انبار استاف (`/warehouses/staff/`) — فقط مالک
- **محصول:** ایجاد/ویرایش محصول و bulk «تنظیم موجودی» از انبار پیش‌فرض و همگام‌سازی `variant.stock` با مجموع انبارها
