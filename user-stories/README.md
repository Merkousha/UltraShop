# User Stories — UltraShop Platform

This folder contains user stories grouped by role. Each story follows a consistent format for traceability and implementation.

## Template

Each user story is written as:

- **Title:** Short, actionable title (verb-first).
- **As a** [role]  
- **I want** [goal/capability]  
- **So that** [business value / outcome]

**Acceptance criteria** (given/when/then or bullet list):

- Criterion 1 (testable).
- Criterion 2 (testable).
- …

**Notes / out of scope:** Optional constraints or future work.

## Role Abbreviations

| Role | Description |
|------|-------------|
| PlatformAdmin | Platform operator; manages stores, config, shipping service, billing. |
| StoreOwner | Merchant who owns one or more stores. |
| StoreStaff | Staff member with limited permissions per store. |
| Customer | End user shopping on a storefront. |

## Folder Structure

```
user-stories/
├── README.md                 (this file + template)
├── platform-admin/
│   ├── auth-and-access.md
│   ├── platform-config.md
│   ├── shipping-service.md
│   └── stores-and-billing.md
├── store-owner/
│   ├── onboarding-and-setup.md
│   ├── catalog-management.md
│   ├── orders-and-fulfillment.md
│   ├── accounting-and-reports.md
│   └── domains-and-branding.md
├── store-staff/
│   ├── orders-and-support.md
│   └── inventory-handling.md
└── customer/
    ├── browsing-and-search.md
    ├── checkout-and-payments.md
    └── orders-and-shipments.md
```

## Usage

- Reference story IDs (e.g. `PA-01`, `SO-02`) in PRD, tickets, and code comments.
- Acceptance criteria should be testable (manual or automated).
- When adding new stories, keep the same format and add to the appropriate role folder.
