# Store Owner — Warehouse Management

Stories for multi-warehouse inventory, smart routing, and inventory forecasting.

---

## SO-50: Create and manage multiple warehouses

**As a** StoreOwner  
**I want** to define multiple warehouses (or storage locations) for my store  
**So that** I can track inventory across different physical locations.

**Acceptance criteria:**

- In "انبارداری" (Warehousing) settings, I can create a warehouse with: name, address (city, state/province, postal code), contact phone, and optional notes.
- I can edit or deactivate a warehouse; deactivating prevents new stock allocations but preserves history.
- Each warehouse is scoped to my store; I can have multiple active warehouses.
- Default warehouse is designated for stores that start with a single location; all existing stock is allocated there.
- Warehouse list shows: name, city, total SKUs stocked, and total units.

---

## SO-51: Allocate inventory across warehouses

**As a** StoreOwner  
**I want** to assign stock quantities per variant per warehouse  
**So that** I know exactly what is available at each location.

**Acceptance criteria:**

- On product/variant detail, I see stock breakdown by warehouse: each warehouse shows its stock quantity for that variant.
- I can adjust stock per warehouse (add/remove units) with an optional reason note (e.g. "دریافت محموله جدید").
- Total variant stock (shown on product list and storefront) is the sum of all warehouse stocks for that variant.
- When an order is fulfilled, stock is deducted from the designated fulfillment warehouse (see SO-52).
- Low-stock alerts respect per-warehouse thresholds if configured, or use the total stock threshold.

---

## SO-52: Use smart routing for order fulfillment

**As a** StoreOwner  
**I want** the system to automatically select the nearest warehouse to the customer for order fulfillment  
**So that** shipping costs are minimized and delivery times are shorter.

**Acceptance criteria:**

- When Smart Routing is enabled (store setting), the system evaluates customer's shipping address against warehouse locations.
- The warehouse with the lowest estimated shipping cost or distance is selected as the fulfillment origin; if that warehouse lacks stock, the next closest with stock is chosen.
- Fulfillment warehouse is shown on order detail and on the shipment creation form (SO-22); I can override the selection manually.
- If all warehouses are out of stock for a line item, the order follows standard out-of-stock handling.
- Smart Routing can be disabled per store; when disabled, the default warehouse is always used.

---

## SO-53: View inventory forecast and restock suggestions

**As a** StoreOwner  
**I want** the system to predict when I need to restock each product based on sales trends  
**So that** I can avoid stockouts and plan purchasing ahead.

**Acceptance criteria:**

- In "پیش‌بینی موجودی" (Inventory Forecast) section, I see a list of products/variants with: current stock, average daily sales rate (calculated from recent order data), and estimated days until stockout.
- Products predicted to run out within a configurable threshold (e.g. 7 or 14 days) are highlighted.
- AI-powered suggestions include: recommended reorder quantity based on historical sales, lead time (if configured), and seasonal trends.
- I can set lead time per product or category (how many days it takes to receive new stock); forecast accounts for this.
- Forecast data is refreshed periodically (e.g. daily) and available on-demand via "بروزرسانی".
- When multi-warehouse is active, forecast is shown per warehouse as well as aggregate.
