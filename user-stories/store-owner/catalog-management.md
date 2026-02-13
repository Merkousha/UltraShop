# Store Owner — Catalog Management

Stories for categories, products, variants, and inventory.

---

## SO-10: Create and manage categories

**As a** StoreOwner  
**I want** to create and manage product categories (with optional parent)  
**So that** my storefront is organized and customers can browse by category.

**Acceptance criteria:**

- I can create a category with: name, optional parent category, description, optional image.
- Slug is auto-generated from name and can be edited; slug must be unique within the store.
- I can reorder categories (e.g. drag-and-drop or sort order field) for display on storefront.
- I can edit or archive a category; archiving does not delete products but hides category from storefront; products can be moved to another category.
- SEO fields (meta title, meta description) are available per category.

---

## SO-11: Create a product with basic info and media

**As a** StoreOwner  
**I want** to create a product with name, description, SKU, categories, and images  
**So that** I can sell it on my storefront.

**Acceptance criteria:**

- Product form includes: name, description (rich text or plain), SKU (unique per store), status (draft/active/archived), one or more categories, and one or more images (upload); first image is primary.
- Slug is auto-generated from name and editable; unique per store.
- Draft products are not visible on storefront; active products are.
- SEO fields (meta title, meta description) are available.
- I can save as draft and publish later.

---

## SO-12: Add variants to a product (e.g. size, color)

**As a** StoreOwner  
**I want** to add variants (e.g. size, color) to a product with separate price and stock  
**So that** I can sell the same product in multiple options.

**Acceptance criteria:**

- On a product I can define option names (e.g. "Size", "Color") and option values (e.g. S, M, L / Red, Blue).
- System generates or I can create variant rows: each variant has SKU, price, optional compare-at price, stock quantity, optional weight.
- Variant SKU is unique per store; at least one variant is required for the product to be sellable.
- Storefront shows variant selector; cart and order store the chosen variant.

---

## SO-13: Manage stock and low-stock alerts

**As a** StoreOwner  
**I want** to update stock per variant and set low-stock threshold for alerts  
**So that** I avoid overselling and get notified when restocking is needed.

**Acceptance criteria:**

- I can edit stock quantity per variant from product/variant list or bulk edit.
- Store settings or product-level "Low stock threshold" can be set; when stock ≤ threshold, dashboard shows a warning (e.g. in products list or a dedicated "Low stock" section).
- When stock reaches zero, variant is not available for purchase (or marked "Out of stock" and not addable to cart) unless "Allow backorder" is enabled (optional feature).
- Stock is decreased when order is confirmed (e.g. on payment); increased on order cancel or refund.

---

## SO-14: Bulk edit products or variants

**As a** StoreOwner  
**I want** to bulk edit products (e.g. change category, status) or variant prices/stock  
**So that** I can save time when managing many items.

**Acceptance criteria:**

- In product list I can select multiple products and apply: change category, set status (draft/active/archived), or delete (soft delete).
- For variants I can select multiple and apply: price change (fixed or percentage), stock adjustment (+/-).
- Bulk action is confirmed (e.g. "Update 5 products?") and result is shown (success count, errors if any).
- Bulk delete or status change is recorded in audit log (optional; at least for delete).

---

## SO-15: Reorder and replace product images

**As a** StoreOwner  
**I want** to reorder product images and set the primary image  
**So that** the best image shows first on the storefront.

**Acceptance criteria:**

- On product edit, images are listed with drag handle or up/down; I can reorder.
- I can mark one image as "Primary"; that image is used in listing and product detail as main image.
- I can remove an image; at least one image is required for an active product (or product cannot be activated until one is added).
