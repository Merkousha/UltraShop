# Store Owner — Domains, Branding & Design System

Stories for custom domain, subdomain, store appearance, theme engine, design tokens, drag-and-drop layout editor, and AI CRO optimization.

---

## SO-40: See my store subdomain and how to use it

**As a** StoreOwner  
**I want** to see my store's subdomain URL and how to share it  
**So that** I can direct customers to my store.

**Acceptance criteria:**

- In store settings, "دامنه" section shows: "فروشگاه شما در آدرس زیر فعال است: `https://<username>.<platform-domain>`".
- Link is clickable and opens the storefront; I am informed that I can also add a custom domain (link to SO-41).
- Subdomain is created automatically when the store is created (SO-02); no extra step required.

---

## SO-41: Add and verify a custom domain

**As a** StoreOwner  
**I want** to add my own domain (e.g. `mystore.com`) and verify ownership  
**So that** my store can be reached at my brand URL.

**Acceptance criteria:**

- In "دامنه" settings I can "افزودن دامنه اختصاصی"; I enter the domain (e.g. `www.mystore.com` or `mystore.com`).
- System shows DNS instructions: "یک رکورد CNAME اضافه کنید: www → username.ultra-shop.com" or A record to platform IP.
- System provides a verification method (TXT record or HTTP file); I click "تأیید" after adding DNS.
- When verification succeeds, domain is marked verified and I can set it as primary storefront domain.
- If verification fails, clear error is shown (e.g. "رکورد TXT یافت نشد؛ مطمئن شوید DNS منتشر شده است").

---

## SO-42: See SSL status for my custom domain

**As a** StoreOwner  
**I want** to see whether my custom domain has a valid SSL certificate  
**So that** I know if customers will see a secure connection.

**Acceptance criteria:**

- For each custom domain, status is shown: "SSL در انتظار", "SSL فعال", "خطای SSL".
- If platform supports automatic SSL (ACME/Let's Encrypt), status updates when certificate is issued; otherwise admin sets manually.
- Storefront is served over HTTPS when SSL is active.

---

## SO-43: Set store branding (logo, colors, basic theme)

**As a** StoreOwner  
**I want** to set my store logo, favicon, and primary color  
**So that** my storefront matches my brand at a basic level.

**Acceptance criteria:**

- Store settings "برندینگ" includes: upload logo (with aspect ratio hint), favicon, and primary color (color picker).
- Changes are saved and storefront reflects them immediately via CSS variables.
- Logo is used in storefront header, emails, and dashboard header when in store context.

---

## SO-44: Choose and customize a theme preset

**As a** StoreOwner  
**I want** to choose a theme preset and see it applied to my storefront  
**So that** I can quickly get a professional look without manual design work.

**Acceptance criteria:**

- In "ظاهر فروشگاه" (Store Appearance) settings, I see available theme presets: مینیمال (Minimal), بولد کامرس (Bold Commerce), الگنت (Elegant), کریِیتور (Creator).
- Each preset shows a preview thumbnail or live preview link; clicking "Preview" shows how my storefront would look with that preset.
- Selecting a preset applies: base typography hierarchy, spacing rhythm, border radius profile, shadow intensity, animation behavior, and component defaults.
- The preset is the foundation; I can further customize via brand override (SO-45).
- Preset change takes effect immediately; no data loss — only visual presentation changes.

---

## SO-45: Customize design tokens and brand overrides

**As a** StoreOwner  
**I want** to customize colors, fonts, radius, and shadow beyond the preset defaults  
**So that** my store's visual identity is unique to my brand.

**Acceptance criteria:**

- From "شخصی‌سازی تم" (Theme Customization), I can modify:
  - Primary color, secondary color, accent color (color pickers with accessibility contrast validation).
  - Heading font and body font (from a curated list with Persian/RTL support; AI may suggest fonts — see SO-07).
  - Corner radius scale (e.g. sharp, rounded, pill).
  - Shadow intensity (e.g. none, subtle, prominent).
  - Button style profile (e.g. filled, outlined, rounded).
- Color changes auto-generate the full scale (50-900) for primary, and system validates WCAG AA contrast.
- If a selected color combination fails contrast check, I see a warning: "کنتراست ناکافی — متن روی این رنگ خوانا نیست".
- Overrides are stored in `StoreTheme` model and compiled to CSS variables per store at runtime.
- Changes are SSR-compatible and cached per domain.

---

## SO-46: Edit storefront layout with drag-and-drop block editor

**As a** StoreOwner  
**I want** to rearrange and configure my storefront layout using a visual drag-and-drop editor  
**So that** I can control what customers see and in what order without coding.

**Acceptance criteria:**

- A "ویرایشگر صفحه" (Page Editor) is available for key pages (home, category, product detail, custom pages).
- Available blocks include: Hero, Product Grid, Category Grid, Banner, Testimonials, FAQ, Newsletter Signup, Custom Section.
- I can: reorder blocks (drag-and-drop), enable/disable individual blocks, and configure per-block settings (e.g. number of products in grid, banner image, heading text).
- Each block respects the store's design tokens (colors, fonts, spacing) and responsive rules.
- Block configuration supports animation rules (e.g. fade-in on scroll) per the Design System spec.
- Layout changes are saved as `LayoutConfiguration` (store, page_type, block_order, block_settings_json) with version tracking.
- I can preview changes before publishing; rollback to a previous layout version is available.
- The editor works on desktop; mobile preview is available to check responsive behavior.

---

## SO-47: Receive AI CRO optimization suggestions

**As a** StoreOwner  
**I want** AI to analyze my storefront and suggest changes that improve conversion rates  
**So that** I can increase sales based on data-driven recommendations.

**Acceptance criteria:**

- In "بهینه‌سازی فروشگاه" (Store Optimization) section, AI analyzes my current storefront and provides actionable suggestions.
- Analysis covers: CTA visibility and contrast, above-the-fold content density, image-to-text ratio, button sizing, scroll depth patterns (if analytics data is available).
- Example recommendations: "اندازه دکمه خرید را ۱۲٪ افزایش دهید", "تصویر هدر را با کنتراست بالاتر جایگزین کنید", "گرید محصولات را از ۶ به ۴ ستون در موبایل تغییر دهید".
- Each suggestion includes: what to change, why (rationale), and expected impact (if applicable).
- I can accept (auto-apply to layout/theme), dismiss, or save for later.
- Suggestions are refreshed periodically or on-demand when I click "تحلیل مجدد".

---

## SO-48: Apply custom CSS to storefront

**As a** StoreOwner  
**I want** to add custom CSS to my storefront for fine-grained visual adjustments  
**So that** I can make specific tweaks beyond theme presets and tokens.

**Acceptance criteria:**

- In store appearance settings, a "CSS سفارشی" field accepts CSS code.
- Custom CSS is sanitized: no inline JS injection, no `@import` to external URLs, CSP-compatible.
- CSS is appended after the theme's compiled CSS, so it can override specific styles.
- CSS bundle including custom CSS remains within performance budget (< 50kb gzipped total).
- Changes are saved in `StoreTheme.custom_css` and applied immediately.
- A clear warning is shown: "CSS نادرست ممکن است ظاهر فروشگاه را خراب کند".
