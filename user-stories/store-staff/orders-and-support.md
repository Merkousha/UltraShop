# Store Staff — Orders & Support

Stories for staff with order and customer support permissions.

---

## SS-01: View orders list (according to my role)

**As a** StoreStaff  
**I want** to view the list of orders for my store  
**So that** I can process fulfillment and answer customer questions.

**Acceptance criteria:**

- I have access to "Orders" in the store dashboard (if my role includes order view).
- Orders list shows: order number, date, customer (or Guest), total, payment status, order status; I can filter by date and status and search by order number or customer.
- I cannot see orders for other stores; only the store(s) I am assigned to.
- If my role does not include orders, I do not see the Orders menu item or get 403 when accessing orders URL.

---

## SS-02: View order detail and timeline

**As a** StoreStaff  
**I want** to open an order and see its details and status timeline  
**So that** I can fulfill it or respond to customer inquiries.

**Acceptance criteria:**

- Clicking an order opens order detail: line items, quantities, prices, shipping address, shipping method, payment reference, and status history (timeline with timestamps).
- I can see customer email/phone (if stored) for support; I cannot edit payment or accounting data.
- Whether I can change order status depends on my role (see SS-03).

---

## SS-03: Update order status (if permitted by role)

**As a** StoreStaff  
**I want** to update order status (e.g. mark as Packed or Shipped) when my role allows  
**So that** I can complete fulfillment without store owner intervention.

**Acceptance criteria:**

- If my role has "Update order status" permission, I see status dropdown or buttons on order detail; I can move order through allowed states (e.g. Paid → Packed → Shipped).
- Valid transitions only (e.g. cannot set to Delivered without Shipped first).
- If my role does not allow status change, I see order detail in read-only mode (no status edit).
- Each status change is recorded with my user and timestamp in the order timeline.

---

## SS-04: Create shipment for an order (platform shipping)

**As a** StoreStaff  
**I want** to create a shipment for an order using platform shipping when my role allows  
**So that** the customer gets tracking and the order is marked Shipped.

**Acceptance criteria:**

- If my role has "Create shipment" or "Fulfill orders" permission, I see "Create shipment" (or "Ship order") on orders that use platform shipping.
- I can enter/confirm carrier and optional weight; submit creates the shipment and updates order with tracking number and status Shipped (or equivalent).
- If my role does not allow this, the action is hidden or returns 403.
- Shipment is created in platform shipping service and linked to this store and order.

---

## SS-05: Look up customer by email or order number

**As a** StoreStaff  
**I want** to search for a customer by email or find an order by order number  
**So that** I can quickly help customers who call or write.

**Acceptance criteria:**

- Search in dashboard (or orders/customers section): by customer email or name returns matching customers and their orders; by order number returns that order.
- I see only data for my store(s); no cross-store data.
- Results show enough info to confirm identity and order (e.g. last orders, total orders) without exposing full payment details beyond what is needed for support.
