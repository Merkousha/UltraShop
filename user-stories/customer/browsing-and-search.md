# Customer — Browsing & Search

Stories for customers browsing the storefront and finding products.

---

## C-01: Browse storefront on subdomain or custom domain

**As a** Customer  
**I want** to open the store via its subdomain (e.g. mystore.ultra-shop.com) or custom domain  
**So that** I can shop at the store I know.

**Acceptance criteria:**

- Visiting `https://<username>.<platform-domain>` or the store's custom domain shows that store's storefront (home, categories, products).
- Store branding (logo, colors, theme) is applied; I do not see other stores' products or data.
- If the store is suspended, I see a clear "Store temporarily unavailable" message instead of the catalog.
- RTL layout and Persian text display correctly when the store uses fa-IR.

---

## C-02: View categories and product listing

**As a** Customer  
**I want** to see categories and a list of products (with image, name, price)  
**So that** I can find what I want to buy.

**Acceptance criteria:**

- Home or main navigation shows categories (as configured by the store); clicking a category shows products in that category.
- Product listing shows: product image, name, price (formatted in store currency, e.g. IRR); optional "Add to cart" or "View" link.
- Only active, in-stock (or backorder-allowed) products are shown; out-of-stock can be hidden or shown with "Out of stock" label per store preference.
- Listing is paginated or infinite scroll; sort options (e.g. newest, price) if the store enables them.

---

## C-03: View product detail with variants

**As a** Customer  
**I want** to open a product and see description, images, and variant options (size, color) with price and stock  
**So that** I can choose the right variant and add to cart.

**Acceptance criteria:**

- Product detail page shows: images (primary + gallery), name, description, variant options (e.g. size dropdown, color swatches); selecting a variant updates price and availability.
- If a variant is out of stock, it is disabled or marked "Out of stock"; I cannot add it to cart unless backorder is allowed.
- "Add to cart" adds the selected variant with chosen quantity; quantity is validated (max available stock or limit per order if set).
- SEO meta (title, description) from the product is used for the page.

---

## C-04: Search products by keyword

**As a** Customer  
**I want** to search products by keyword  
**So that** I can find items without browsing categories.

**Acceptance criteria:**

- A search box is available (header or dedicated search page); I enter a keyword and submit.
- Results show matching products (name, description, or SKU) from this store only; same listing format as category view (image, name, price).
- No results shows a clear message; search is scoped to the current store only.
- Optional: search suggestions or recent searches (stored in session only).

---

## C-05: Add products to cart and see cart summary

**As a** Customer  
**I want** to add products to cart and see a cart summary (count, total)  
**So that** I can continue browsing or go to checkout.

**Acceptance criteria:**

- After "Add to cart", I see confirmation (e.g. toast or cart drawer); cart icon or link shows item count and optionally subtotal.
- Cart summary (drawer or page) lists: product, variant, quantity, price, line total; I can change quantity or remove a line.
- Cart is persisted by session (and by account if I am logged in); I can leave and return and see the same cart (within session/account scope and expiry).
- Prices and totals are in store currency (IRR) with correct formatting.
