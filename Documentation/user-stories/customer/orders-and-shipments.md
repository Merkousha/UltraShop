# Customer — Orders & Shipments

Stories for order history, shipment tracking, and notifications. **Viewing orders requires login via phone + OTP** for the store (see checkout-and-payments C-09).

---

## C-20: View my order history (when logged in with phone+OTP)

**As a** Customer  
**I want** to see my past orders when I am logged in with my phone and OTP  
**So that** I can check status and reorder or get support.

**Acceptance criteria:**

- When logged in (phone+OTP for this store), "سفارش‌های من" shows a list of my orders for this store: order number, date, total, status (e.g. پرداخت‌شده، ارسال‌شده، تحویل‌شده).
- I can filter or search by order number or date; clicking an order opens order detail.
- I see only my own orders for this store; no other customers' data.
- If I am not logged in, I am redirected to the **phone + OTP login** flow with a return URL to the orders page.

---

## C-21: View order detail and status

**As a** Customer  
**I want** to open an order and see its details and current status  
**So that** I know what I bought and whether it has shipped.

**Acceptance criteria:**

- Order detail shows: order number, date, status, line items (product name, variant, quantity, price), shipping address, shipping method, payment method, and total.
- Status timeline is visible with timestamps for each state transition (pending, paid, packed, shipped, delivered).
- If shipped, tracking number or "پیگیری مرسوله" link is shown (see C-22).
- I can only view orders that belong to my account (order list and detail are scoped by current customer and store).

---

## C-22: Track my shipment

**As a** Customer  
**I want** to track my shipment when the store has provided a tracking number  
**So that** I know when to expect delivery.

**Acceptance criteria:**

- On order detail, if the order has a shipment with tracking number, I see "پیگیری مرسوله" or the tracking number as a link.
- Clicking opens a tracking view: either in-app (status and events from platform shipping service) or redirect to carrier tracking page if configured.
- Tracking shows events such as: ایجاد شده، برداشت شده، در حال ارسال، تحویل داده شده (or equivalent); dates/times are shown in a Jalali calendar format.
- If tracking is not available yet, I see "اطلاعات پیگیری پس از ارسال بسته در دسترس خواهد بود" or similar.
- When Smart Routing is active, the shipment origin warehouse is automatically selected based on proximity to my address.

---

## C-23: Receive order and shipping notifications

**As a** Customer  
**I want** to receive email (or SMS) when my order is confirmed and when it is shipped  
**So that** I have a record and can track without logging in.

**Acceptance criteria:**

- After order is created and paid, I receive an order confirmation email (to the email provided at checkout) with order number, summary, and link to view order.
- When store marks order as Shipped and tracking is added, I receive a shipping notification with tracking number and link.
- Emails are sent from the platform/store config (from name, reply-to); content is clear and includes store name and order reference.
- Optional: SMS notification for order confirmation and shipping updates if the platform and store support it.
- Notification content uses the store's branding (logo, colors) when applicable.
