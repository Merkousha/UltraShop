---
description: "Use when working on shipping, shipment tracking, carrier management, or shipment state transitions."
---
# Shipping & Shipment Guidelines

## Shipment State Machine
Valid statuses: `created` → `picked_up` → `in_transit` → `delivered` | `exception`

Allowed transitions (defined in `Shipment.ALLOWED_TRANSITIONS`):
```
created    → [picked_up]
picked_up  → [in_transit, exception]
in_transit → [delivered, exception]
exception  → [in_transit, delivered]
```

- Always validate with `shipment.can_transition_to(new_status)` before changing
- When shipment reaches `delivered`, update associated order status to `delivered`
- Log all status changes via `core.services.log_action()`

## Global Toggle
- `PlatformSettings.shipping_enabled` — toggles entire shipping service
- Check this flag before creating shipments or processing shipping operations
