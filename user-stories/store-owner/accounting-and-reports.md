# Store Owner — Accounting & Reports

Stories for per-store accounting, balance, and payouts.

**Implementation:** Ledger (SO-30), revenue/expense summary by period (SO-31), balance and payout request (SO-32), and ledger export CSV with date range (SO-33) are implemented. Payout approval in admin calls `post_payout_approved`.

---

## SO-30: View my store ledger and journals

**As a** StoreOwner  
**I want** to view my store's ledger and journal entries  
**So that** I have a clear picture of revenue, expenses, and balances.

**Acceptance criteria:**

- Dashboard or "Accounting" section has a ledger view: list of journal entries (date, description, account, debit/credit, balance or running total).
- I can filter by date range and by account (e.g. revenue, expenses, platform commission, shipping, receivables).
- Entries are read-only; they are created automatically by the system (order paid, refund, shipping fee, commission, payout).
- Optional: export to CSV for my own records.

---

## SO-31: View revenue and expense summary

**As a** StoreOwner  
**I want** to see a summary of revenue and expenses (e.g. by period)  
**So that** I can understand my store's profitability.

**Acceptance criteria:**

- A report or dashboard widget shows: total revenue (from orders) in selected period, total expenses (refunds, shipping, commission), and net (or balance).
- Period selector: today, this week, this month, custom range.
- Data is derived from the same ledger (no separate aggregation that could diverge).
- Optional: simple chart (e.g. revenue over time).

---

## SO-32: View my store balance and request payout

**As a** StoreOwner  
**I want** to see my store's available balance and request a payout (withdrawal)  
**So that** I can receive my earnings.

**Acceptance criteria:**

- "Balance" or "Payouts" section shows: current available balance (from ledger), and list of past payout requests (date, amount, status: Pending, Approved, Rejected).
- I can submit a new payout request: amount (cannot exceed available balance), and payment details (e.g. bank account number, shaba, or reference as configured by platform).
- After submission, request appears as Pending; platform admin can approve or reject (PA-33).
- When approved, balance is debited and I see the updated balance and request status.

---

## SO-33: Export accounting or order report

**As a** StoreOwner  
**I want** to export accounting or order data (e.g. CSV) for a date range  
**So that** I can use it for my own bookkeeping or taxes.

**Acceptance criteria:**

- From ledger or reports I can "Export" with date range; file format is CSV (or Excel if supported).
- Ledger export includes: date, description, account, debit, credit, balance (or similar columns).
- Optional: orders export with order number, date, customer, total, status for the same period.
- Export is generated server-side and downloaded; large exports may be queued and emailed (optional for v1).
