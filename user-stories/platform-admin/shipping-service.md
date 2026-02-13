# Platform Admin — Shipping Service

Stories for the central platform shipping service used by stores.

**Implementation:** PA-21: `shipping.ShippingCarrier` model (name, code, is_active, api_credentials). Platform admin CRUD at `/platform/carriers/` (list, add, edit, delete). Stores can use carrier list when creating shipments (carrier selection can be wired in shipment form later).

---

## PA-20: Enable or disable platform shipping for the whole platform

**As a** PlatformAdmin  
**I want** to enable or disable the platform shipping service globally  
**So that** I can turn off shipping during maintenance or migration without affecting store settings.

**Acceptance criteria:**

- A global toggle "Platform shipping service enabled" exists in platform admin.
- When disabled, no store can use platform shipping for new orders; existing shipments can still be viewed/tracked.
- Store-facing shipping method selection does not show platform shipping when the service is disabled.
- Change is logged in audit log.

---

## PA-21: Configure shipping carriers and rates (platform level)

**As a** PlatformAdmin  
**I want** to configure which carriers and rate rules the platform shipping service uses  
**So that** all stores using platform shipping get consistent options and pricing.

**Acceptance criteria:**

- Platform admin has a section "Shipping carriers" (or "Shipping service config") where carriers can be added/edited (name, code, optional API credentials).
- Rate rules or zones (e.g. by weight, by region) can be configured so that shipping cost can be calculated or suggested.
- Stores that use platform shipping see the same carrier options (or a subset) at checkout; store owner cannot add arbitrary carriers at store level for platform shipping (store-specific methods like "pickup" are separate).

---

## PA-22: View all shipments and delivery status

**As a** PlatformAdmin  
**I want** to view all shipments created via the platform shipping service and their status  
**So that** I can monitor operations and resolve delivery issues.

**Acceptance criteria:**

- A list view of shipments with filters: store, date range, status (created, picked up, in transit, delivered, exception).
- Each row shows: shipment id, store, order reference, carrier, tracking number, status, created/updated dates.
- Drill-down to shipment detail shows full history (events) and linked order(s).
- Data is read-only; status updates come from carrier integration or manual update by designated process.

---

## PA-23: Manually update shipment status when needed

**As a** PlatformAdmin  
**I want** to manually update a shipment's status (e.g. mark as delivered) when carrier data is missing or wrong  
**So that** stores and customers see accurate tracking and we can close fulfillment.

**Acceptance criteria:**

- On shipment detail, an action "Update status" is available with allowed next states (e.g. mark as delivered, mark as exception).
- Manual update records the actor and timestamp; optionally a note (e.g. "Customer confirmed receipt").
- Manual updates are recorded in audit log.
- Store and customer-facing tracking view reflect the updated status.
