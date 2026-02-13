# Store Owner — Orders & Fulfillment

Stories for viewing orders, updating status, and using platform shipping.

**Implementation note:** SO-20 (list/filter orders), SO-21 (update status + timeline), SO-22 (create shipment from order, track), SO-23 (refund), and SO-24 (cancel with stock restore) are implemented. Status changes (including cancel, refund, paid, shipped) are recorded in `OrderStatusEvent` and shown as a timeline on order detail with timestamp and actor (SO-21).

---

## SO-20: View and filter orders

**As a** StoreOwner  
**I want** to view a list of orders with filters (date, status, customer)  
**So that** I can manage fulfillment and support customers.

**Acceptance criteria:**

- Orders list shows: order number, date, customer (or "Guest"), total, payment status, order status (e.g. Pending, Paid, Packed, Shipped, Delivered, Cancelled).
- I can filter by: date range, order status, payment status; and search by order number or customer email/name.
- Clicking an order opens order detail: line items, shipping address, shipping method, payment reference, status history, and actions (e.g. update status, create shipment, refund).

---

## SO-21: Update order status through lifecycle

**As a** StoreOwner  
**I want** to update order status (e.g. Paid → Packed → Shipped → Delivered)  
**So that** customers and my team see accurate order state and accounting stays correct.

**Acceptance criteria:**

- On order detail I can change status via dropdown or buttons; only valid transitions are allowed (e.g. cannot set to Shipped before Paid).
- Status options: Pending, Paid, Packed, Shipped, Delivered, Cancelled, Refunded (full/partial can be separate or note).
- Each status change is recorded with timestamp (and optionally actor for staff); visible in order timeline.
- When order moves to Paid, accounting posting is triggered (revenue, receivables); when Shipped/Delivered, shipping-related logic runs if using platform shipping.

---

## SO-22: Create a shipment using platform shipping

**As a** StoreOwner  
**I want** to create a shipment for an order using the platform shipping service  
**So that** the shipment is tracked centrally and the customer gets tracking info.

**Acceptance criteria:**

- For an order that has a shipping method "Platform shipping" (or equivalent), I have an action "Create shipment" (or "Ship order").
- I can enter or confirm: carrier (from platform-configured list), package weight/dimensions if required; system may calculate cost or use fixed rate.
- On confirm, a shipment record is created in the platform shipping service linked to this order (and store); I get a tracking number if the carrier returns one.
- Order status can be set to Shipped and tracking number is stored; customer and store can view tracking status.
- If platform shipping is disabled globally, "Create shipment" is not available for platform shipping method; I can still mark as Shipped with a manual tracking note (store-level only).

---

## SO-23: Issue full or partial refund

**As a** StoreOwner  
**I want** to issue a full or partial refund for an order  
**So that** I can correct overcharges or handle returns.

**Acceptance criteria:**

- On order detail I have "Refund" action; I can choose full or partial (amount or by line item).
- Reason (optional) and amount are recorded; refund is processed via payment gateway if applicable (or marked as manual/offline).
- Order status can be set to Refunded (or partial refund is recorded and order remains in appropriate state).
- Accounting receives automatic posting: reversal of revenue and receivables, refund expense or liability; store balance is updated if applicable.
- Refund is logged in audit log.

---

## SO-24: Cancel an order before fulfillment

**As a** StoreOwner  
**I want** to cancel an order (e.g. before shipping) and optionally trigger refund  
**So that** I can stop orders I cannot fulfill.

**Acceptance criteria:**

- I can cancel an order from order detail; only orders in cancellable state (e.g. Pending, Paid but not Shipped) can be cancelled.
- On cancel I can choose: "Refund customer" (triggers refund flow) or "Cancel without refund" (e.g. payment failed); if refund is chosen, SO-23 refund flow applies.
- Order status is set to Cancelled; stock is restored for cancelled items.
- Cancellation is recorded in order timeline and audit log.
