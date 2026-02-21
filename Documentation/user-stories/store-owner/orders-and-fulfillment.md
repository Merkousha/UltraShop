# Store Owner — Orders & Fulfillment

Stories for viewing orders, updating status, shipping, and refunds. Smart Routing from multi-warehouse is integrated when applicable (see warehouse-management.md).

---

## SO-20: View and filter orders

**As a** StoreOwner  
**I want** to view a list of orders with filters (date, status, customer)  
**So that** I can manage fulfillment and support customers.

**Acceptance criteria:**

- Orders list shows: order number, date, customer (or "مهمان"), total, payment status, order status (e.g. در انتظار، پرداخت‌شده، بسته‌بندی، ارسال‌شده، تحویل‌شده، لغو‌شده).
- I can filter by: date range, order status, payment status; and search by order number or customer phone/name.
- Clicking an order opens order detail: line items, shipping address, shipping method, payment reference, status timeline, and actions (update status, create shipment, refund).
- When multi-warehouse is active, orders show the designated fulfillment warehouse.

---

## SO-21: Update order status through lifecycle

**As a** StoreOwner  
**I want** to update order status (e.g. Paid → Packed → Shipped → Delivered)  
**So that** customers and my team see accurate order state and accounting stays correct.

**Acceptance criteria:**

- On order detail I can change status via dropdown or buttons; only valid transitions are allowed (e.g. cannot set to Shipped before Paid).
- Status options: Pending, Paid, Packed, Shipped, Delivered, Cancelled, Refunded.
- Each status change is recorded as an `OrderStatusEvent` with timestamp and actor; visible in order timeline.
- When order moves to Paid, accounting posting is triggered (revenue, receivables, platform commission); when Shipped, shipping-related logic runs.
- Customer receives notification on key status changes (if configured).

---

## SO-22: Create a shipment using platform shipping

**As a** StoreOwner  
**I want** to create a shipment for an order using the platform shipping service  
**So that** the shipment is tracked centrally and the customer gets tracking info.

**Acceptance criteria:**

- For an order using platform shipping, I have "ایجاد مرسوله" (Create Shipment) action.
- I can enter or confirm: carrier (from platform-configured list), optional tracking number, package weight/dimensions if required.
- On confirm, a shipment record is created in the platform shipping service linked to this order (and store); tracking number is stored.
- Order status is set to Shipped; customer and store can view tracking status.
- When multi-warehouse with Smart Routing is active, the shipment origin warehouse is pre-selected based on customer proximity (see SO-52).
- If platform shipping is disabled globally, I can still mark as Shipped with a manual tracking note.
- Shipping notification email is sent to the customer when a shipment is created.

---

## SO-23: Issue full or partial refund

**As a** StoreOwner  
**I want** to issue a full or partial refund for an order  
**So that** I can correct overcharges or handle returns.

**Acceptance criteria:**

- On order detail I have "استرداد وجه" (Refund) action; I can choose full or partial (amount or by line item).
- Reason (optional) and amount are recorded; `Order.refunded_amount` is updated.
- Order status is set to Refunded when fully refunded; partial refund is recorded and order remains in appropriate state.
- Accounting receives automatic posting: reversal of revenue and receivables; store balance is updated.
- Refund is logged in audit log with actor, amount, and reason.

---

## SO-24: Cancel an order before fulfillment

**As a** StoreOwner  
**I want** to cancel an order (e.g. before shipping) and optionally trigger refund  
**So that** I can stop orders I cannot fulfill.

**Acceptance criteria:**

- I can cancel an order from order detail; only orders in cancellable state (Pending or Paid, not yet Shipped) can be cancelled.
- On cancel I can choose: "استرداد وجه" (Refund customer, triggers SO-23 refund flow) or "لغو بدون استرداد" (Cancel without refund).
- Order status is set to Cancelled; stock is restored for all cancelled line items.
- Cancellation is recorded as `OrderStatusEvent` in order timeline and in audit log.
