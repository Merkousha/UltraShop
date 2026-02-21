# Store Owner — Accounting & Reports

Stories for per-store accounting, balance, payouts, OCR expense scanning, financial health, and AI CFO agent.

---

## SO-30: View my store ledger and journals

**As a** StoreOwner  
**I want** to view my store's ledger and journal entries  
**So that** I have a clear picture of revenue, expenses, and balances.

**Acceptance criteria:**

- Dashboard "حسابداری" section has a ledger view: list of journal entries (date, description, account, debit/credit, balance or running total).
- I can filter by date range and by account (e.g. revenue, expenses, platform commission, shipping, receivables).
- Entries are read-only; they are created automatically by the system (order paid, refund, shipping fee, commission, payout).
- Double-entry bookkeeping: every transaction has balanced debit and credit entries.

---

## SO-31: View revenue and expense summary

**As a** StoreOwner  
**I want** to see a summary of revenue and expenses (e.g. by period)  
**So that** I can understand my store's profitability.

**Acceptance criteria:**

- A report or dashboard widget shows: total revenue (from orders) in selected period, total expenses (refunds, shipping, commission), and net profit.
- Period selector: today, this week, this month, custom range.
- Data is derived from the same ledger (no separate aggregation that could diverge).
- Optional: simple chart (e.g. revenue over time, expense breakdown by category).

---

## SO-32: View my store balance and request payout

**As a** StoreOwner  
**I want** to see my store's available balance and request a payout (withdrawal)  
**So that** I can receive my earnings.

**Acceptance criteria:**

- "موجودی و برداشت" section shows: current available balance (from ledger), and list of past payout requests (date, amount, status: در انتظار, تأیید شده, رد شده).
- I can submit a new payout request: amount (cannot exceed available balance), and payment details (e.g. شماره شبا, bank account number).
- After submission, request appears as Pending; platform admin can approve or reject (PA-33).
- When approved, balance is debited and I see the updated balance and request status.

---

## SO-33: Export accounting or order report

**As a** StoreOwner  
**I want** to export accounting or order data (e.g. CSV) for a date range  
**So that** I can use it for my own bookkeeping or taxes.

**Acceptance criteria:**

- From ledger or reports I can "خروجی CSV" with date range; file format is CSV (or Excel if supported).
- Ledger export includes: date, description, account, debit, credit, balance (or similar columns).
- Optional: orders export with order number, date, customer, total, status for the same period.
- Export is generated server-side and downloaded; large exports may be queued and emailed (optional for v1).

---

## SO-34: Scan and record expense invoices (OCR)

**As a** StoreOwner  
**I want** to scan or photograph physical purchase invoices and have them automatically recorded in my expenses  
**So that** I can track all costs without manual data entry.

**Acceptance criteria:**

- From "هزینه‌ها" (Expenses) in accounting, I can click "اسکن فاکتور" and upload a photo or PDF of a physical invoice.
- OCR AI extracts: vendor name, date, total amount, line items (if readable), and tax amount.
- Extracted data is shown in a form for review; I can correct any misread fields before confirming.
- On confirm, a `StoreTransaction` is created as an expense entry with the invoice details; the original image is stored as an attachment.
- The expense is categorized automatically (e.g. "خرید کالا", "هزینه حمل") based on content; I can change the account/category.
- If OCR cannot extract reliably, it shows what it found and leaves the rest for manual entry.

---

## SO-35: View financial health dashboard

**As a** StoreOwner  
**I want** to see a financial health overview including net profit, cash flow, and tax estimates  
**So that** I understand my business performance at a glance.

**Acceptance criteria:**

- "سلامت مالی" (Financial Health) section shows: net profit (revenue - all expenses) for the current period, cash flow summary (income vs outgoing), and estimated tax liability (based on configurable tax rate).
- Key indicators are displayed with trend arrows (compared to previous period).
- If cash flow is negative or net profit is declining, a warning banner is shown.
- Data is derived from the ledger; period selector is available (this month, this quarter, this year).
- Optional: comparison charts (this period vs. previous period).

---

## SO-36: Receive AI CFO agent reports and alerts

**As a** StoreOwner  
**I want** an AI agent to periodically analyze my store's financials and alert me to issues  
**So that** I can act on problems (declining profit, unusual expenses) before they become critical.

**Acceptance criteria:**

- The AI CFO Agent runs periodic analysis (e.g. weekly) on my store's ledger, orders, and financial data.
- It generates a summary report visible in my dashboard: key findings, trends, and actionable recommendations (e.g. "سود ناخالص ۱۵٪ کاهش یافته؛ بررسی هزینه ارسال توصیه می‌شود").
- Critical alerts are highlighted: profitability drop below threshold, unusual expense spikes, negative cash flow, high refund rates.
- I can view past reports in a history list; each report includes the analysis date and a summary.
- I can configure alert thresholds (e.g. minimum profit margin) or disable the agent.
- The agent does not take any automatic financial actions; it only reports and recommends.
