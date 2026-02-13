# Store Staff — Inventory Handling

Stories for staff with inventory permissions.

---

## SS-10: View products and variant stock

**As a** StoreStaff  
**I want** to view products and their variant stock levels  
**So that** I can answer stock questions and know what to pack.

**Acceptance criteria:**

- I have access to "Products" or "Inventory" (if my role includes inventory view).
- I can see product list with name, SKU, status, and variant stock (e.g. total or per-variant); low-stock items are highlighted if store has low-stock alerts.
- I can open a product to see variant-level stock; I cannot edit product name, price, or catalog structure unless my role allows (see SS-11).
- Data is limited to my store(s).

---

## SS-11: Update variant stock (if permitted)

**As a** StoreStaff  
**I want** to update stock quantity for variants when my role allows  
**So that** I can correct counts after physical inventory or receive new stock.

**Acceptance criteria:**

- If my role has "Edit inventory" or "Update stock" permission, I can edit stock quantity per variant (from product detail or a quick-edit list).
- I cannot change price, SKU, or product structure; only quantity.
- Change is saved and reflected immediately; optional: adjustment reason or note for audit (e.g. "Stock take 2025-02-01").
- If my role does not allow stock edit, I see stock in read-only mode.

---

## SS-12: View low-stock report

**As a** StoreStaff  
**I want** to see a list of products or variants that are low or out of stock  
**So that** I can inform the owner or restock.

**Acceptance criteria:**

- A "Low stock" or "Inventory alerts" view lists variants (or products) where stock ≤ threshold (set by store owner) or stock = 0.
- I can see variant name, SKU, current stock, threshold; link to product for more detail.
- I can update stock from this list if my role allows (SS-11).
- If my role does not include inventory, I do not see this section.
