---
description: "Use when creating or editing Django views, URL patterns, or handling form submissions. Covers CBV patterns, access mixins, and multi-tenancy."
applyTo: "**/views.py"
---
# Django Views Guidelines

## Class-Based Views
- All views are CBVs extending `TemplateView`, `ListView`, `DetailView`, or `View`
- Process form data via `request.POST` directly in `post()` method
- File uploads via `request.FILES` / `request.FILES.getlist("field_name")`

## Access Mixins
- **Dashboard views:** Use `StoreAccessMixin` (from `dashboard.views`) — requires login + store ownership/staff
- **Platform admin views:** Use `PlatformAdminMixin` (from `platform_admin.views`) — requires PlatformAdmin group
- **Storefront views:** Use `StoreMixin` (from `storefront.views`) — resolves store from URL `store_username`

## Multi-Tenancy in Views
- Dashboard: `request.current_store` set by `StoreAccessMixin` from session `current_store_id`
- Storefront: `self.store` set by `StoreMixin` from URL kwarg
- ALWAYS filter querysets by store: `Model.objects.filter(store=self.store)`

## Pagination
- Products: 25 per page
- Orders: 25 per page
- Accounting ledger: 50 per page
- Storefront search: 20 per page

## URL Naming
- Namespaced: `accounts`, `dashboard`, `platform_admin`, `storefront`
- In templates: `{% url 'namespace:view-name' %}` (e.g., `{% url 'dashboard:product-list' %}`)
- Slugified names with hyphens (e.g., `product-list`, `order-detail`, `store-settings`)

## Audit Logging
- For platform admin state-changing actions, call `core.services.log_action(user, store, action, resource_type, resource_id, details)`
- Actions: string like `"update_settings"`, `"toggle_shipping"`, `"update_shipment_status"`
