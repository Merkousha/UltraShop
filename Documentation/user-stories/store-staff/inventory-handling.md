# Store Staff — Inventory Handling

Stories for staff with inventory permissions. Includes multi-warehouse support when enabled.

---

## SS-10: View products and variant stock

**As a** StoreStaff  
**I want** to view products and their variant stock levels  
**So that** I can answer stock questions and know what to pack.

**Acceptance criteria:**

- I have access to "محصولات" or "موجودی" (if my role includes inventory view).
- I can see product list with name, SKU, status, and variant stock (total or per-variant); low-stock items are highlighted if store has low-stock alerts.
- When multi-warehouse is enabled, I can see stock breakdown by warehouse for each variant.
- I can open a product to see variant-level stock; I cannot edit product name, price, or catalog structure unless my role allows.
- Data is limited to my store(s).

---

## SS-11: Update variant stock (if permitted)

**As a** StoreStaff  
**I want** to update stock quantity for variants when my role allows  
**So that** I can correct counts after physical inventory or receive new stock.

**Acceptance criteria:**

- If my role has "Edit inventory" permission, I can edit stock quantity per variant (from product detail or a quick-edit list).
- When multi-warehouse is enabled, I select which warehouse to adjust and enter the quantity change.
- I cannot change price, SKU, or product structure; only quantity.
- Change is saved and reflected immediately; optional: adjustment reason or note for audit (e.g. "شمارش فیزیکی ۱۴۰۳/۱۲/۰۱").
- If my role does not allow stock edit, I see stock in read-only mode.

---

## SS-12: View low-stock report

**As a** StoreStaff  
**I want** to see a list of products or variants that are low or out of stock  
**So that** I can inform the owner or restock.

**Acceptance criteria:**

- A "کالاهای رو به اتمام" view lists variants where stock ≤ threshold or stock = 0.
- I can see variant name, SKU, current stock, threshold; link to product for more detail.
- When multi-warehouse is enabled, low-stock report shows per-warehouse breakdown.
- I can update stock from this list if my role allows (SS-11).
- If my role does not include inventory, I do not see this section.

---

## SS-13: Handle warehouse-specific stock (if permitted)

**As a** StoreStaff  
**I want** to view and adjust stock at my assigned warehouse  
**So that** I can manage inventory at my physical location accurately.

**Acceptance criteria:**

- When multi-warehouse is active and my role includes warehouse access, I see a warehouse-filtered view of inventory.
- I can adjust stock for variants at my warehouse (receive stock, count adjustments) with a reason note.
- I cannot modify stock at warehouses I am not assigned to (if warehouse-level access control is enabled).
- Stock adjustments are reflected in the total variant stock and in the inventory forecast (SO-53).
