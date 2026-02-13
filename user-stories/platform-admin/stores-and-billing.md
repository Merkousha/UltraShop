# Platform Admin — Stores & Billing

Stories for managing stores and platform-level billing/settlements.

**Implementation:** Stores list with search and status filter (PA-30), store detail with balance/order/shipment counts and Suspend/Reactivate (PA-31, PA-32). Payout list with Approve/Reject (PA-33). Commission report at `/platform/commission/` with date range and per-store breakdown (PA-34); requires `PLATFORM_COMMISSION_RATE` &gt; 0 for new orders.

---

## PA-30: List and search all stores

**As a** PlatformAdmin  
**I want** to list all stores with search and basic filters  
**So that** I can find a store by name, username, or owner and manage it.

**Acceptance criteria:**

- Platform admin has a "Stores" list with columns: store name, username (subdomain), owner email, status (active/suspended), created date.
- I can search by store name or username (partial match).
- I can filter by status (e.g. active only).
- Clicking a store opens store detail or store-level admin view (read-only or limited actions as defined).

---

## PA-31: View store detail and key metrics

**As a** PlatformAdmin  
**I want** to view a store's detail and key metrics (order count, revenue, shipping usage)  
**So that** I can assess store health and support issues.

**Acceptance criteria:**

- Store detail page shows: profile (name, username, domain(s)), owner, created date, settings summary (time zone, currency).
- Key metrics displayed: total orders (count), revenue (from store accounting or order aggregate), number of shipments via platform shipping in a period.
- No ability to edit store catalog or orders from platform admin (those stay in store dashboard); only view and platform-level actions (e.g. suspend, billing).

---

## PA-32: Suspend or reactivate a store

**As a** PlatformAdmin  
**I want** to suspend or reactivate a store  
**So that** I can enforce policy or stop abuse without deleting data.

**Acceptance criteria:**

- Store detail has actions "Suspend" and "Reactivate" (depending on current state).
- When suspended: storefront returns a "Store temporarily unavailable" (or similar) message; store dashboard login still works but may show a banner; new orders are not accepted.
- When reactivated, storefront and checkout work again.
- Suspend/reactivate is recorded in audit log with actor and reason (optional field).

---

## PA-33: View and approve store payout (withdrawal) requests

**As a** PlatformAdmin  
**I want** to see store withdrawal requests and approve or reject them  
**So that** stores receive their balance according to platform policy.

**Acceptance criteria:**

- A "Payout requests" or "Withdrawals" section lists pending requests: store, amount, requested at, payment details (e.g. bank account or reference).
- I can approve or reject a request; on approval, system records payout in store ledger and updates store balance; on rejection, store is notified and can resubmit or edit details.
- Approved payouts are logged; optional export for accounting (e.g. CSV).

---

## PA-34: View platform-level revenue and commission summary

**As a** PlatformAdmin  
**I want** to view platform-level revenue and commission summary (e.g. total commission from all stores in a period)  
**So that** I can report on platform performance.

**Acceptance criteria:**

- A dashboard or report shows: total commission earned (from store accounting postings) in a date range, optionally per-store breakdown.
- Data is derived from stored accounting entries (no double-counting); date filter is applied consistently.
- Export (e.g. CSV) is available for further analysis.
