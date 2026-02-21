# Platform Admin — Stores & Billing

Stories for managing stores, platform-level billing, settlements, and commission.

---

## PA-30: List and search all stores

**As a** PlatformAdmin  
**I want** to list all stores with search and basic filters  
**So that** I can find a store by name, username, or owner and manage it.

**Acceptance criteria:**

- "فروشگاه‌ها" list at `/platform/stores/` with columns: store name, username (subdomain), owner email, status (active/suspended), created date.
- I can search by store name or username (partial match).
- I can filter by status (active, suspended, all).
- Clicking a store opens store detail page.

---

## PA-31: View store detail and key metrics

**As a** PlatformAdmin  
**I want** to view a store's detail and key metrics (order count, revenue, shipping usage)  
**So that** I can assess store health and support issues.

**Acceptance criteria:**

- Store detail page shows: profile (name, username, domain(s)), owner, created date, settings summary (time zone, currency, theme preset).
- Key metrics displayed: total orders (count), store balance, number of shipments via platform shipping, and total commission earned from this store.
- No ability to edit store catalog or orders from platform admin; only view and platform-level actions (suspend, payout management).

---

## PA-32: Suspend or reactivate a store

**As a** PlatformAdmin  
**I want** to suspend or reactivate a store  
**So that** I can enforce policy or stop abuse without deleting data.

**Acceptance criteria:**

- Store detail has "تعلیق" (Suspend) and "فعال‌سازی مجدد" (Reactivate) actions depending on current state.
- When suspended: storefront shows "فروشگاه موقتاً غیرفعال است" page; store dashboard login still works but may show a banner; new orders are not accepted.
- When reactivated, storefront and checkout work again immediately.
- Suspend/reactivate is recorded in audit log with actor and optional reason.

---

## PA-33: View and approve store payout (withdrawal) requests

**As a** PlatformAdmin  
**I want** to see store withdrawal requests and approve or reject them  
**So that** stores receive their balance according to platform policy.

**Acceptance criteria:**

- "درخواست‌های برداشت" section lists pending requests: store, amount, requested date, payment details (bank account / شبا).
- I can approve or reject a request; on approval, `post_payout_approved` is called (debit from store balance, record in ledger); on rejection, store is notified and can resubmit.
- Approved payouts are logged in audit log; optional CSV export for bank processing.

---

## PA-34: View platform-level revenue and commission summary

**As a** PlatformAdmin  
**I want** to view platform-level revenue and commission summary (total commission from all stores in a period)  
**So that** I can report on platform performance.

**Acceptance criteria:**

- Commission report at `/platform/commission/` shows: total commission earned in a date range, with per-store breakdown.
- Commission is calculated from `PlatformCommission` records (created on each order paid, based on `PLATFORM_COMMISSION_RATE`).
- Date filter is applied consistently; data is derived from stored records (no double-counting).
- CSV export is available for further analysis.

---

## PA-35: View platform dashboard with key KPIs

**As a** PlatformAdmin  
**I want** to see a platform-level dashboard with key performance indicators  
**So that** I can monitor overall platform health at a glance.

**Acceptance criteria:**

- Platform dashboard (landing page after login) shows: total active stores, total orders (today/this week/this month), total pending payouts, total commission earned, and active shipments count.
- Key alerts are highlighted: stores with issues (e.g. high refund rates), pending payouts nearing SLA, shipping exceptions.
- Dashboard data is refreshed on page load; optional auto-refresh interval.
- Links from each KPI lead to the relevant detail page (stores, payouts, commission, shipments).
