---
description: "Use when working on the accounting system, financial transactions, commission calculations, payout processing, or store balance queries."
---
# Accounting & Financial Guidelines

## Transaction Model
- `StoreTransaction`: positive amount = credit (revenue), negative = debit (commission, refund, payout)
- Types: `revenue`, `expense`, `commission`, `refund`, `payout`, `shipping`
- Balance = sum of all transaction amounts for a store

## Services (accounting/services.py)
- `get_store_balance(store)` — aggregate all StoreTransaction amounts
- `post_order_paid(order)` — creates: revenue transaction (net), commission debit transaction, PlatformCommission record
- `post_order_refunded(order, amount, reason)` — creates refund debit transaction
- `post_payout_approved(payout_request)` — creates payout debit transaction

## Commission
- Rate from `settings.PLATFORM_COMMISSION_RATE` (default 5%)
- Auto-deducted from order revenue when `post_order_paid()` is called
- Tracked in `PlatformCommission` model (store, order, amount)

## Currency
- All amounts in IRR (Iranian Rial) — integer, no decimals
- Use `PositiveBigIntegerField` for storage
- Format with thousands separator for display
