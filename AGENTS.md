# UltraShop — Project Guidelines

## Overview

UltraShop is a **multi-tenant SaaS e-commerce platform** for B2C merchants in Iran.
Built with **Django 5.x**, **Python 3.12**, **Tailwind CSS** (local standalone JS build), and **Vazirmatn** font.

- **Locale:** fa-IR, Asia/Tehran, RTL layout, IRR currency (PositiveBigIntegerField, no decimals)
- **Database:** SQLite3 (dev), all schemas multi-tenant with explicit `store` FK
- **Auth:** Custom email-based User (`core.User`), PlatformAdmin group, phone+OTP for customers
- **Dev server:** `python manage.py runserver 8080` (port 8000 restricted)
- **Seed data:** `python manage.py seed_platform` → creates PlatformAdmin group, settings, superuser (`admin@ultra-shop.com` / `Admin@12345`)

## Architecture

```
10 Django apps:
  core           → Users, Stores, Domains, PlatformSettings, AuditLog, StoreStaff
  catalog        → Category, Product, ProductImage, ProductVariant
  customers      → Customer (per-store), LoginOTP
  orders         → Order, OrderLine, OrderStatusEvent
  shipping       → ShippingCarrier, Shipment (state machine)
  accounting     → StoreTransaction, PayoutRequest, PlatformCommission
  payments       → Payment (gateway abstraction)
  platform_admin → Platform admin panel views (PlatformAdminMixin)
  dashboard      → Store owner/staff dashboard views (StoreAccessMixin)
  storefront     → Customer-facing store pages (StoreMixin)
```

### URL Namespaces

| Path | Namespace | Purpose |
|------|-----------|---------|
| `/` | `home` | Landing page |
| `/platform/` | `platform_admin` | Platform admin panel |
| `/accounts/` | `accounts` | Login/logout |
| `/dashboard/` | `dashboard` | Store owner/staff dashboard |
| `/s/<store_username>/` | `storefront` | Customer-facing storefront |
| `/admin/` | — | Django admin |

### Multi-Tenancy Pattern

- Every tenant model has an explicit `store` FK
- `StoreMiddleware` resolves store from Host header for subdomain/custom domain
- Storefront URLs: `/s/<store_username>/...`
- Dashboard: session-based store selection (`current_store_id`)

## Code Style

- **Language:** Python code and git commits in English. UI text and templates in Persian (RTL)
- **Views:** Class-based views. Form data processed via `request.POST` directly (no Django Form classes used yet)
- **Templates:** Extend `base.html` or app-specific base. Use `{% load static %}` for local assets. Tailwind CSS for styling
- **Models:** Timestamps via `auto_now_add`/`auto_now`. Unicode slugs. `PositiveBigIntegerField` for IRR amounts
- **Mixins:** `StoreAccessMixin` (dashboard), `PlatformAdminMixin` (platform_admin), `StoreMixin` (storefront)
- **Audit:** Use `core.services.log_action()` for platform admin actions
- **Encryption:** Use `core.encryption.encrypt_value()` / `decrypt_value()` for sensitive fields (API keys, passwords)

## Build and Test

```bash
# Activate venv
.\.venv\Scripts\Activate.ps1          # Windows PowerShell

# Check for issues
python manage.py check

# Run server
python manage.py runserver 8080

# Migrations
python manage.py makemigrations
python manage.py migrate

# Seed platform data
python manage.py seed_platform
```

## Conventions

- **Static assets are LOCAL** — no CDN references. All JS/CSS/fonts served from `static/`
- **URL references in templates:** Always use namespaced `{% url 'namespace:name' %}` (e.g., `{% url 'accounts:login' %}`)
- **Currency:** IRR stored as integer (PositiveBigIntegerField), no decimal
- **Accounting:** Positive amount = credit, negative = debit on `StoreTransaction`
- **Shipment state machine:** Use `Shipment.ALLOWED_TRANSITIONS` dict, validate with `can_transition_to()`
- **Commission:** Auto-calculated at `PLATFORM_COMMISSION_RATE` (default 5%) via `accounting.services.post_order_paid()`
- **Persian text:** Use Vazirmatn font. All user-facing text in Persian. `dir="rtl"` on HTML root

## Documentation

- [Documentation/PRD.md](Documentation/PRD.md) — Full product requirements
- [Documentation/DesignSystem-PRD.md](Documentation/DesignSystem-PRD.md) — Design system vision
- [Documentation/user-stories/](Documentation/user-stories/) — User stories by role
- [Documentation/sprints/](Documentation/sprints/) — Sprint breakdown (sprint-01 through sprint-09)
