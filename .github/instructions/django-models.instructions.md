---
description: "Use when creating or editing Django models, writing migrations, or changing database schema. Covers multi-tenancy, currency, slug, and naming conventions."
applyTo: "**/models.py"
---
# Django Models Guidelines

## Multi-Tenancy
- Every tenant-scoped model MUST have a `store = models.ForeignKey("core.Store", on_delete=models.CASCADE)`
- Add unique constraints scoped to store where needed: `unique_together = [("store", "slug")]`
- Never query tenant models without filtering by store

## Currency (IRR)
- Use `models.PositiveBigIntegerField()` for all monetary amounts — IRR has no decimals
- Field names: `price`, `amount`, `cost`, `compare_at_price`, `refunded_amount`

## Naming Conventions
- Table name via `class Meta: db_table = "plural_snake_case"` (e.g., `products`, `order_lines`)
- FK fields: singular noun (e.g., `store`, `order`, `customer`)
- M2M fields: plural noun (e.g., `categories`)
- Boolean fields: `is_*` or `allow_*` prefix (e.g., `is_active`, `allow_guest_checkout`)

## Slugs
- Use `models.SlugField(allow_unicode=True)` for Persian content
- Auto-generate slug from name in `save()` using `slugify(self.name, allow_unicode=True)`

## Timestamps
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`

## Status Fields
- Use `models.CharField` with `choices` — define choices as tuples at class level
- Example statuses: `draft/active/archived` (products), `pending/paid/packed/shipped/delivered/cancelled/refunded` (orders)

## Encryption
- Sensitive fields (API keys, passwords): store encrypted via `core.encryption.encrypt_value()`
- Name the field `*_encrypted` (e.g., `sms_api_key_encrypted`, `email_password_encrypted`)
