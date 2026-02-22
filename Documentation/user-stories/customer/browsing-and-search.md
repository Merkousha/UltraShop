# Customer — Browsing & Search

Stories for customers browsing the storefront, finding products, and interacting with the AI support agent.

---

## C-01: Browse storefront on subdomain or custom domain

**As a** Customer  
**I want** to open the store via its subdomain (e.g. `mystore.ultra-shop.com`) or custom domain  
**So that** I can shop at the store I know.

**Acceptance criteria:**

- Visiting `https://<username>.<platform-domain>` or the store's verified custom domain shows that store's storefront (home, categories, products).
- Store branding (logo, colors, fonts, theme preset) is applied via the Design System token layer; I do not see other stores' products or data.
- The storefront layout reflects the store's configured block order (hero, product grid, banners, etc.) as set in the drag-and-drop editor.
- If the store is suspended, I see a clear "فروشگاه موقتاً غیرفعال است" message instead of the catalog.
- RTL layout and Persian text display correctly; typography follows the store's heading/body font configuration.
- Page loads within performance budget (LCP < 2.5s on 4G); critical CSS is inlined for above-the-fold content.

---

## C-02: View categories and product listing

**As a** Customer  
**I want** to see categories and a list of products (with image, name, price)  
**So that** I can find what I want to buy.

**Acceptance criteria:**

- Home or main navigation shows categories (as configured by the store owner); clicking a category shows products in that category.
- Product listing shows: product image, name, price (formatted in store currency, e.g. IRR with correct separator); optional "Add to cart" or "View" link.
- Only active, in-stock (or backorder-allowed) products are shown; out-of-stock items can be hidden or displayed with "ناموجود" label per store preference.
- Listing is paginated or infinite scroll; sort options (e.g. newest, price low-to-high, price high-to-low) available.
- AI-generated SEO meta tags and alt text are rendered for each product and category page.
- Product listing respects the store's theme tokens (card background, text color, spacing rhythm).

---

## C-03: View product detail with variants

**As a** Customer  
**I want** to open a product and see description, images, and variant options (size, color) with price and stock  
**So that** I can choose the right variant and add to cart.

**Acceptance criteria:**

- Product detail page shows: images (primary + gallery), name, full description (AI-generated or manually written), variant options (e.g. size dropdown, color swatches); selecting a variant updates price and availability.
- If a variant is out of stock, it is disabled or marked "ناموجود"; I cannot add it to cart unless backorder is allowed.
- "Add to cart" adds the selected variant with chosen quantity; quantity is validated (max available stock or limit per order if set).
- SEO meta (title, description, alt text) from the product is used for the page; AI-generated copy is indistinguishable from manual content.
- Product attributes extracted by Vision-to-Listing (material, color, dimensions) are displayed in a structured format if available.

---

## C-04: Search products by keyword

**وضعیت:** ✅ انجام شد

**As a** Customer  
**I want** to search products by keyword  
**So that** I can find items without browsing categories.

**Acceptance criteria:**

- A search box is available in the storefront header; I enter a keyword and submit.
- Results show matching products (name, description, SKU, or AI-generated attributes) from this store only; same listing format as category view (image, name, price).
- No results shows a clear "محصولی یافت نشد" message; search is scoped to the current store only.
- Optional: search suggestions or recent searches (stored in session only).
- Search respects product status: only active products are returned.

---

## C-05: Add products to cart and see cart summary

**As a** Customer  
**I want** to add products to cart and see a cart summary (count, total)  
**So that** I can continue browsing or go to checkout.

**Acceptance criteria:**

- After "Add to cart", I see confirmation (e.g. toast or cart drawer); cart icon or link shows item count and optionally subtotal.
- Cart summary (drawer or page) lists: product, variant, quantity, price, line total; I can change quantity or remove a line.
- Cart is persisted by session (and by customer account if I am logged in); I can leave and return and see the same cart (within session/account scope and expiry).
- Prices and totals are in store currency (IRR) with correct formatting.
- Stock is validated on cart update; if stock has changed since adding, I see a warning.

---

## C-06: Get help from AI Support Agent

**As a** Customer  
**I want** to ask questions about products, orders, or store policies via an AI chatbot  
**So that** I can get instant answers without waiting for human support.

**Acceptance criteria:**

- A chat widget or "پشتیبانی" button is available on the storefront (if enabled by the store owner).
- The AI Support Agent can answer questions about: product availability (connected to real-time inventory), order status (if I provide order number or am logged in), store policies (shipping, returns), and general product information.
- Responses are in Persian (fa-IR) and contextually relevant to the current store's catalog and policies.
- If the agent cannot answer, it offers to connect me to human support or provides the store's contact information.
- Chat history is maintained within my session; I can scroll back to see previous messages.
- The agent does not disclose other customers' data or internal store metrics.
