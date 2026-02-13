# Store Owner — Domains & Branding

Stories for custom domain, subdomain, and store appearance.

**Implementation:** Subdomain URL shown in settings (SO-40). Custom domain add with DNS instructions (CNAME to subdomain), Verify and Set primary (SO-41); SSL status field (SO-42, manual for v1). Branding: logo, favicon, primary_color, theme_preset (SO-43). Middleware resolves verified custom domain to store.

---

## SO-40: See my store subdomain and how to use it

**As a** StoreOwner  
**I want** to see my store's subdomain URL and how to share it  
**So that** I can direct customers to my store.

**Acceptance criteria:**

- In store settings, "Domain" or "Store URL" section shows: "Your store is available at: https://<username>.<platform-domain>" (e.g. https://mystore.ultra-shop.com).
- Link is clickable and opens the storefront; I am informed that I can also add a custom domain (link to SO-41).
- Subdomain is created automatically when the store is created (SO-02); no extra step required.

---

## SO-41: Add and verify a custom domain

**As a** StoreOwner  
**I want** to add my own domain (e.g. mystore.com) and verify ownership  
**So that** my store can be reached at my brand URL.

**Acceptance criteria:**

- In "Domain" settings I can "Add custom domain"; I enter the domain (e.g. www.mystore.com or mystore.com).
- System shows DNS instructions: e.g. "Add a CNAME record: www → username.ultra-shop.com" or "Add an A record to our IP".
- System provides a verification method (e.g. TXT record to add, or HTTP file at known path); I click "Verify" after adding DNS.
- When verification succeeds, domain is marked verified and I can set it as primary (or only) storefront domain; storefront is then accessible via custom domain (and optionally still via subdomain).
- If verification fails, clear error is shown (e.g. "TXT record not found; ensure DNS has propagated").

---

## SO-42: See SSL status for my custom domain

**As a** StoreOwner  
**I want** to see whether my custom domain has a valid SSL certificate  
**So that** I know if customers will see a secure connection.

**Acceptance criteria:**

- For each custom domain, status is shown: e.g. "SSL pending", "SSL active", "SSL error" (with short message if available).
- If platform supports automatic SSL (e.g. Let's Encrypt), status updates when certificate is issued or renewed; otherwise admin may set manually and status reflects that.
- Storefront should be served over HTTPS when SSL is active; if not yet active, platform may show a notice or fallback to subdomain (product decision).

---

## SO-43: Set store branding (logo, colors, theme)

**As a** StoreOwner  
**I want** to set my store logo, colors, and choose a theme preset  
**So that** my storefront matches my brand.

**Acceptance criteria:**

- Store settings include "Branding": upload logo (with crop or aspect ratio hint), favicon, and primary/accent color (color picker or preset).
- Theme presets (Tailwind-based) are available: e.g. "Default", "Minimal", "Bold"; selecting one applies a set of Tailwind classes or CSS variables to the storefront.
- Changes are saved and storefront preview (or live storefront) reflects them immediately.
- Logo and colors are used in storefront header, emails (if applicable), and dashboard header when in store context.
