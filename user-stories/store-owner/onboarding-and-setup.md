# Store Owner — Onboarding & Setup

Stories for store registration, first-time setup, and store management.

---

## SO-01: Sign up as a store owner

**As a** StoreOwner  
**I want** to sign up with my email or phone and create a platform account  
**So that** I can create and manage my store(s).

**Acceptance criteria:**

- Sign-up page is available on the central domain (e.g. `ultra-shop.com/register`).
- I can register with email and password, or phone and password (or OTP); required fields are validated.
- Email or phone verification is required before I can create a store (e.g. verification link or code).
- After verification, I am logged in and can access "Create store" or dashboard to add a store.
- Password policy (length, complexity) is enforced; password is stored hashed.

---

## SO-02: Create my first store with a username (subdomain)

**As a** StoreOwner  
**I want** to create my first store and choose a unique username that becomes my store subdomain  
**So that** my store is available at `username.ultra-shop.com` without extra setup.

**Acceptance criteria:**

- "Create store" flow asks for: store name, username (subdomain part), optional short description.
- Username is validated: allowed characters (e.g. lowercase letters, numbers, hyphen), length limits, and checked against reserved/blacklist list; uniqueness is enforced.
- On success, store is created and subdomain is provisioned (or queued): store is reachable at `username.<platform-domain>` for storefront and dashboard.
- I see a confirmation message with the store URL and a link to continue setup (e.g. add products, set payment).

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

- In store settings, there is a "Team" or "Staff" section where I can invite by email.
- I select a role for the invitee (e.g. "Orders & support", "Inventory", "Full access except billing"); roles are predefined with clear permission sets.
- Invitation is sent by email with a link; accepting creates a store-staff association and allows login to this store's dashboard with that role.
- I can revoke access or change role later; changes take effect on next request (or session refresh).
- Invitation and role changes are recorded in audit log (visible to platform admin).

---

## SO-05: Set store basics (time zone, currency, guest checkout)

**As a** StoreOwner  
**I want** to set my store's time zone, display currency, and whether to allow guest checkout  
**So that** dates, prices, and checkout behavior match my business.

**Acceptance criteria:**

- Store settings include: time zone (for order dates and reports), display currency (default IRR; formatted correctly), and "Allow guest checkout" (on/off).
- When guest checkout is off, customers must register or log in before completing checkout.
- Changes are saved and applied immediately to storefront and new orders.
- Default values come from platform defaults if set by platform admin.
