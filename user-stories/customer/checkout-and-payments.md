# Customer — Checkout & Payments

Stories for checkout flow and payment. **Customer login is phone + OTP only** (no email/password for customers).

**Implementation:** Online payment (C-11) is implemented: order confirmation shows "پرداخت آنلاین"; redirect to gateway (mock or ZarinPal), callback sets order Paid and posts to accounting. **Cash on delivery (COD)** is deferred / out of current scope.

---

## C-09: Log in with phone and OTP (when store requires)

**As a** Customer  
**I want** to log in (or register) using my mobile number and a one-time code sent by SMS  
**So that** I can complete checkout when the store does not allow guest checkout, or to see my order history.

**Acceptance criteria:**

- I see "ورود / ثبت‌نام با موبایل" (or equivalent); I enter my phone number and submit.
- I receive an OTP by SMS (or see a mock message in development); I am shown a form to enter the code.
- When I enter the correct code before it expires, I am logged in for this store only; my session is scoped to this store (e.g. `customer_id_{store_id}`).
- If I enter a wrong code, I see an error; after a limited number of attempts (e.g. 5), I must request a new code (see C-09b).
- I am not told whether my phone was "already registered"; the same flow works for first-time (register) and returning (login) customers.

---

## C-09b: Request a new OTP or handle lockout

**As a** Customer  
**I want** to request a new OTP if I did not receive it or if I exceeded verify attempts  
**So that** I can complete login.

**Acceptance criteria:**

- I can go back to the phone entry step and submit again to receive a new code; previous unused codes for that phone are invalidated.
- Rate limiting applies: I cannot request more than N OTPs per phone (and optionally per IP) in a short window (e.g. 3 per 60 seconds); if exceeded, I see a clear message to wait.
- After too many failed verify attempts, I see a message that I must request a new code; I can do so from the same flow.

---

## C-10: Enter shipping address and choose shipping method

**As a** Customer  
**I want** to enter my shipping address and choose a shipping method at checkout  
**So that** my order is delivered correctly and I know the cost.

**Acceptance criteria:**

- Checkout step (or page) collects: full name, phone, address (street, city, state/province, postal code as needed for the store's region).
- If I am logged in (via phone+OTP), I can select a saved address or add a new one and save for next time (when that feature exists).
- Shipping methods are shown: e.g. "Platform shipping" (with cost if calculated or "Calculated at next step"), "Pickup", "Local delivery" (if store offers them).
- I select one method; total updates if shipping has a cost; I can proceed to payment step.

---

## C-11: Choose payment method and complete payment

**As a** Customer  
**I want** to choose a payment method and complete payment  
**So that** my order is confirmed and paid.

**Acceptance criteria:**

- Checkout shows payment methods (e.g. "Online payment", "Cash on delivery" if enabled by store).
- For online payment: I am redirected to the gateway (or see embedded form); after success I am redirected back to the store with an order confirmation page; if failure, I see an error and can retry or change method.
- For cash on delivery: I confirm order and see confirmation without gateway redirect; order is created in "Pending" or "Awaiting payment" until store marks it (or COD is treated as confirmed per store policy).
- Order confirmation page shows: order number, line items, total, shipping address, and next steps (e.g. "We'll send tracking when shipped").

---

## C-12: Check out as guest (if store allows)

**As a** Customer  
**I want** to check out without logging in when the store allows guest checkout  
**So that** I can buy quickly without phone+OTP.

**Acceptance criteria:**

- If store has "Allow guest checkout" enabled, I can proceed to checkout without logging in; I enter shipping details (name, phone, address) only; no OTP is required.
- Order is created and linked to the phone (and optionally email if collected); I receive order confirmation by SMS/email if the store sends it.
- If guest checkout is disabled, I am prompted to log in with **phone + OTP** before I can reach the address or payment step; after login I return to checkout with cart preserved.
- Guest orders are visible to the store by phone/order number; customer can later "claim" or view order by logging in with the same phone (optional for v1).

---

## C-13: Log in with phone+OTP during checkout (when required)

**As a** Customer  
**I want** to log in with my phone and OTP when the store requires a customer account for checkout  
**So that** I can complete my purchase and have order history.

**Acceptance criteria:**

- If I am not logged in and the store has disabled guest checkout, I am redirected to the **phone + OTP** login flow (see C-09); a "next" URL brings me back to checkout (address or review step) after successful login.
- There is no separate "registration" form; the same phone+OTP flow creates my customer record for this store on first use (register) and logs me in on later use.
- After a successful order, my order appears in "My account" / "Orders" when I am logged in (phone+OTP session for this store).
- Session is kept so I stay logged in for this store across visits (within session expiry).
