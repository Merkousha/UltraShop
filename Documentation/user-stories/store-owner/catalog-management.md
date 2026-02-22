# Store Owner — Catalog Management

Stories for categories, products, variants, inventory, and AI-powered content generation.

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
- SEO fields (meta title, meta description) are available per category; AI can auto-generate them (see SO-17).

---

## SO-11: Create a product with basic info and media

**As a** StoreOwner  
**I want** to create a product with name, description, SKU, categories, and images  
**So that** I can sell it on my storefront.

**Acceptance criteria:**

- Product form includes: name, description (rich text or plain), SKU (unique per store), status (draft/active/archived), one or more categories, and one or more images (upload); first image is primary.
- Slug is auto-generated from name and editable; unique per store.
- Draft products are not visible on storefront; active products are.
- SEO fields (meta title, meta description) are available; AI can auto-generate them (see SO-17).
- I can save as draft and publish later.

---

## SO-12: Add variants to a product (e.g. size, color)

**As a** StoreOwner  
**I want** to add variants (e.g. size, color) to a product with separate price and stock  
**So that** I can sell the same product in multiple options.

**Acceptance criteria:**

- On a product I can define option names (e.g. "سایز", "رنگ") and option values (e.g. S, M, L / قرمز, آبی).
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
- Store settings or product-level "Low stock threshold" can be set; when stock ≤ threshold, dashboard shows a warning (e.g. in products list or a dedicated "کالاهای رو به اتمام" section).
- When stock reaches zero, variant is not available for purchase (or marked "ناموجود") unless "Allow backorder" is enabled.
- Stock is decreased when order is confirmed (on payment); increased on order cancel or refund.
- When multi-warehouse is enabled, stock is tracked per warehouse per variant (see SO-51).

---

## SO-14: Bulk edit products or variants

**وضعیت:** ⚠️ نیمه‌کامل
**کمبودها:** حذف نرم، ثبت در audit log، و نمایش نتیجه عملیات (success/errors) هنوز پیاده‌سازی نشده است.

**As a** StoreOwner  
**I want** to bulk edit products (e.g. change category, status) or variant prices/stock  
**So that** I can save time when managing many items.

**Acceptance criteria:**

- In product list I can select multiple products and apply: change category, set status (draft/active/archived), or delete (soft delete).
- For variants I can select multiple and apply: price change (fixed or percentage), stock adjustment (+/-).
- Bulk action is confirmed (e.g. "آیا ۵ محصول بروزرسانی شود؟") and result is shown (success count, errors if any).
- Bulk delete or status change is recorded in audit log.

---

## SO-15: Reorder and replace product images

**وضعیت:** ✅ انجام شد

**As a** StoreOwner  
**I want** to reorder product images and set the primary image  
**So that** the best image shows first on the storefront.

**Acceptance criteria:**

- On product edit, images are listed with drag handle or up/down; I can reorder.
- I can mark one image as "Primary"; that image is used in listing and product detail as main image.
- I can remove an image; at least one image is required for an active product.

---

## SO-16: Create product listing from photo (Vision-to-Listing)

**As a** StoreOwner  
**I want** to upload a product photo and have AI automatically extract product attributes  
**So that** I can create listings quickly without typing every detail manually.

**Acceptance criteria:**

- From the "Add product" or a dedicated "لیست‌سازی هوشمند" page, I can upload one or more product photos.
- AI analyzes each photo and extracts: suggested product name, material/fabric type, colors, approximate dimensions or size, and category suggestion.
- Extracted attributes are populated in the product creation form as pre-filled (editable) fields; I can review and correct before saving.
- AI-generated description (from visual attributes) is shown as a suggestion that I can accept, edit, or discard.
- Multiple photos trigger per-photo analysis; all are added to the product gallery with the first as primary.
- Processing time is shown (loading indicator); if AI cannot extract attributes, it shows what it found and leaves the rest blank.

---

## SO-17: Auto-generate SEO content for products and categories

**As a** StoreOwner  
**I want** AI to generate meta titles, meta descriptions, product descriptions, and image alt text  
**So that** my store ranks better in search engines without manual SEO work.

**Acceptance criteria:**

- For each product or category, I can click "تولید سئو خودکار" (Auto SEO) to generate: meta title, meta description, and image alt text.
- AI uses the product name, description, category, and attributes to generate relevant, keyword-rich content in Persian.
- Product description (copywriting) can also be generated: I click "تولید توضیحات" and AI writes a compelling product description based on the product's attributes and photos.
- Generated content fills the respective fields as suggestions; I can review, edit, or regenerate before saving.
- Bulk SEO generation is available: I select multiple products and click "تولید سئو دسته‌ای"; AI generates meta content for all selected items.

---

## SO-18: Use AI content calendar for campaigns and discounts

**As a** StoreOwner  
**I want** AI to suggest optimal timing for discounts, campaigns, and content publication  
**So that** I maximize sales impact with data-driven scheduling.

**Acceptance criteria:**

- A "تقویم محتوا" (Content Calendar) section in the dashboard shows: upcoming suggested events (e.g. seasonal sales, holidays, suggested discount windows).
- AI suggests campaigns based on: store's sales trends, product seasonality, industry norms, and upcoming holidays/events relevant to the store's market.
- Each suggestion includes: recommended date range, discount percentage or type, target products or categories, and a brief reason.
- I can accept a suggestion (creates a scheduled campaign/discount), modify it, or dismiss it.
- Calendar view shows both AI-suggested and manually created campaigns on a timeline.
