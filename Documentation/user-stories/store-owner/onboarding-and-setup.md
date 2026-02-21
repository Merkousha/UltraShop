# Store Owner — Onboarding & Setup

Stories for store registration, AI-assisted onboarding, first-time setup, and store management.

---

## SO-01: Sign up as a store owner

**As a** StoreOwner  
**I want** to sign up with my email and create a platform account  
**So that** I can create and manage my store(s).

**Acceptance criteria:**

- Sign-up page is available on the central domain (e.g. `ultra-shop.com/register`).
- I register with email and password; required fields are validated.
- Email verification is required before I can create a store (verification link sent).
- After verification, I am logged in and can access "Create store" or dashboard.
- Password policy (minimum length, complexity) is enforced; password is stored hashed (PBKDF2 or Argon2).

---

## SO-02: Create my first store with a username (subdomain)

**As a** StoreOwner  
**I want** to create my first store and choose a unique username that becomes my store subdomain  
**So that** my store is available at `username.ultra-shop.com` without extra setup.

**Acceptance criteria:**

- "Create store" flow asks for: store name, username (subdomain part), optional short description.
- Username is validated: allowed characters (lowercase letters, numbers, hyphen), length limits, and checked against reserved/blacklist list; uniqueness is enforced.
- On success, store is created and subdomain is provisioned: store is reachable at `username.<platform-domain>` for storefront and dashboard.
- I see a confirmation message with the store URL and a link to continue setup (AI wizard or manual setup).

---

## SO-03: Log in to my store dashboard

**As a** StoreOwner  
**I want** to log in and reach my store dashboard via subdomain or central domain  
**So that** I can manage my store from a single place.

**Acceptance criteria:**

- I can log in from the central domain; after login I can select a store and be redirected to that store's dashboard (e.g. `username.ultra-shop.com/dashboard`).
- I can also go directly to `username.ultra-shop.com/dashboard` (or `/login` on that subdomain); after login I am in that store's context.
- Dashboard shows store name and quick links: orders, products, accounting, settings.
- If I own multiple stores, I can switch store context from the dashboard (store switcher).

---

## SO-04: Invite staff and assign roles

**As a** StoreOwner  
**I want** to invite staff members and assign them roles (e.g. orders only, inventory only)  
**So that** my team can help without full access to accounting or settings.

**Acceptance criteria:**

- In store settings, there is a "تیم" or "کارکنان" section where I can invite by email.
- I select a role for the invitee (e.g. "staff", "manager"); roles have predefined permission sets (staff: orders/inventory; manager: all except accounting/settings).
- The invited user must already have a platform account; adding them creates a store-staff association.
- I can revoke access or change role later; changes take effect on next request.
- Staff additions and role changes are recorded in audit log.

---

## SO-05: Set store basics (time zone, currency, guest checkout)

**As a** StoreOwner  
**I want** to set my store's time zone, display currency, and whether to allow guest checkout  
**So that** dates, prices, and checkout behavior match my business.

**Acceptance criteria:**

- Store settings include: time zone (for order dates and reports), display currency (default IRR; formatted correctly with thousands separator), and "Allow guest checkout" toggle.
- When guest checkout is off, customers must log in with phone+OTP before completing checkout.
- Changes are saved and applied immediately to storefront and new orders.
- Default values come from platform defaults if set by platform admin.

---

## SO-06: Complete AI-assisted onboarding wizard

**As a** StoreOwner  
**I want** to set up my store through a conversational AI wizard that asks about my business  
**So that** I can get a professional store running in minutes without technical knowledge.

**Acceptance criteria:**

- After creating my store (SO-02), I can choose to start the "راه‌اندازی هوشمند" (AI Setup Wizard).
- The wizard asks me (via chat-like interface) about: business name, industry/category, target audience, and visual preferences (style, mood).
- Based on my answers, the wizard automatically suggests: a theme preset, primary/secondary colors, heading/body fonts, and initial layout block configuration.
- I can review and accept or modify each suggestion before applying.
- The wizard completes within 5 minutes; at the end, my store has a functional storefront with branding applied.
- I can skip the wizard and set up manually at any time.

---

## SO-07: Generate brand identity with AI

**As a** StoreOwner  
**I want** the AI to generate a logo, color palette, and font combination based on my brand description  
**So that** I have a professional visual identity without hiring a designer.

**Acceptance criteria:**

- From store settings or during onboarding, I can request "تولید هویت بصری" (AI Brand Generation).
- I provide: brand name, industry, brand tone (e.g. مدرن، کلاسیک، خلاقانه), and optionally upload a reference image.
- AI generates: logo suggestions (at least 2-3 options), a full color palette (primary 50-900 scale, neutral, success, warning, error), and a heading/body font pair.
- I can preview each suggestion applied to a storefront mockup before accepting.
- Accepted brand identity is saved to my `StoreTheme` and immediately reflected on the storefront.
- Font suggestions consider Persian-first support and RTL compatibility.
