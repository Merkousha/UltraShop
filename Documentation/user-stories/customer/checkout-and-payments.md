# Customer — Checkout & Payments

Stories for checkout flow and payment. **Customer login is phone + OTP only** (no email/password for customers).

---

## C-09: Log in with phone and OTP (when store requires)

**As a** Customer  
**I want** to log in (or register) using my mobile number and a one-time code sent by SMS  
**So that** I can complete checkout when the store does not allow guest checkout, or to see my order history.

**Acceptance criteria:**

- I see "ورود / ثبت‌نام با موبایل" (or equivalent); I enter my phone number and submit.
- I receive an OTP by SMS (or see a mock message in development); I am shown a form to enter the code.
- When I enter the correct code before it expires (e.g. 5 minutes), I am logged in for this store only; my session is scoped to this store (e.g. `customer_id_{store_id}`).
- If I enter a wrong code, I see an error; after a limited number of attempts (e.g. 5), I must request a new code (see C-09b).
- I am not told whether my phone was "already registered"; the same flow works for first-time (register) and returning (login) customers.
- Customer identity is per (store, phone): the same phone number is a separate customer in each store.

---

## C-09b: Request a new OTP or handle lockout

**As a** Customer  
**I want** to request a new OTP if I did not receive it or if I exceeded verify attempts  
**So that** I can complete login.

**Acceptance criteria:**

- I can go back to the phone entry step and submit again to receive a new code; previous unused codes for that phone are invalidated.
- Rate limiting applies: I cannot request more than N OTPs per phone (and optionally per IP) in a short window (e.g. 3 per 60 seconds); if exceeded, I see a clear message to wait.
- After too many failed verify attempts, I see a message that I must request a new code; I can do so from the same flow.
- No information about whether the phone is registered is disclosed.

---

## C-10: Enter shipping address and choose shipping method

**As a** Customer  
**I want** to enter my shipping address and choose a shipping method at checkout  
**So that** my order is delivered correctly and I know the cost.

**Acceptance criteria:**

- Checkout step collects: full name, phone, address (street, city, state/province, postal code).
- If I am logged in (via phone+OTP), I can select a saved address or add a new one and save for next time (when that feature exists).
- Shipping methods are shown: e.g. "ارسال پلتفرم" (platform shipping, with cost if calculated), "تحویل حضوری" (pickup), "ارسال محلی" (local delivery) — as configured by the store.
- When the store uses multi-warehouse with Smart Routing, the nearest warehouse to my address is automatically selected for fulfillment; the shipping cost reflects the optimized route.
- I select one method; total updates if shipping has a cost; I can proceed to payment step.

---

## C-11: Choose payment method and complete payment

**As a** Customer  
**I want** to choose a payment method and complete payment  
**So that** my order is confirmed and paid.

**Acceptance criteria:**

- Checkout shows available payment methods (e.g. "پرداخت آنلاین", "پرداخت در محل" if enabled by store).
- For online payment: I am redirected to the gateway (mock or ZarinPal); after success I am redirected back to the store with an order confirmation page; on failure, I see an error and can retry or change method.
- For cash on delivery (if enabled): I confirm order and see confirmation without gateway redirect; order is created in "Pending" status.
- Order confirmation page shows: order number, line items, total, shipping address, estimated delivery, and next steps (e.g. "پس از ارسال، کد پیگیری برایتان ارسال می‌شود").
- On successful payment, accounting postings are triggered automatically (revenue, receivables, platform commission).

---

## C-12: Check out as guest (if store allows)

**As a** Customer  
**I want** to check out without logging in when the store allows guest checkout  
**So that** I can buy quickly without phone+OTP.

**Acceptance criteria:**

- If store has "Allow guest checkout" enabled, I can proceed to checkout without logging in; I enter shipping details (name, phone, address) and optionally email; no OTP is required.
- Order is created and linked to the phone; I receive order confirmation by email (if provided) or SMS (if store sends it).
- If guest checkout is disabled, I am prompted to log in with **phone + OTP** before I can reach the address or payment step; after login I return to checkout with cart preserved.
- Guest orders are visible to the store by phone/order number; customer can later view order by logging in with the same phone (optional for v1).

---

## C-13: Log in with phone+OTP during checkout (when required)

**As a** Customer  
**I want** to log in with my phone and OTP when the store requires a customer account for checkout  
**So that** I can complete my purchase and have order history.

**Acceptance criteria:**

- If I am not logged in and the store has disabled guest checkout, I am redirected to the **phone + OTP** login flow (see C-09); a "next" URL brings me back to checkout (address or review step) after successful login.
- There is no separate "registration" form; the same phone+OTP flow creates my customer record for this store on first use and logs me in on later use.
- After a successful order, my order appears in "سفارش‌های من" when I am logged in (phone+OTP session for this store).
- Session is kept so I stay logged in for this store across visits (within session expiry).
