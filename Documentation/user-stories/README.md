# User Stories — UltraShop Platform

This folder contains user stories grouped by role. Each story follows a consistent format for traceability and implementation. Stories cover the full scope of both PRDs: the multi-tenant e-commerce platform and the Enterprise Design System & Theme Engine.

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
| PlatformAdmin | Platform operator; manages stores, config, shipping service, billing, design system governance, and AI settings. |
| StoreOwner | Merchant who owns one or more stores; full control over products, staff, accounting, domains, branding, theme, and AI features. |
| StoreStaff | Staff member with limited permissions per store (e.g. orders, inventory, support). |
| Customer | End user shopping on a storefront. |

## Folder Structure

```
user-stories/
├── README.md                 (this file + template)
├── platform-admin/
│   ├── auth-and-access.md        (PA-01 to PA-04)
│   ├── platform-config.md        (PA-10 to PA-15)
│   ├── shipping-service.md       (PA-20 to PA-23)
│   └── stores-and-billing.md     (PA-30 to PA-35)
├── store-owner/
│   ├── onboarding-and-setup.md   (SO-01 to SO-07)
│   ├── catalog-management.md     (SO-10 to SO-18)
│   ├── orders-and-fulfillment.md (SO-20 to SO-24)
│   ├── accounting-and-reports.md (SO-30 to SO-36)
│   ├── domains-and-branding.md   (SO-40 to SO-48)
│   └── warehouse-management.md   (SO-50 to SO-53)
├── store-staff/
│   ├── orders-and-support.md     (SS-01 to SS-05)
│   └── inventory-handling.md     (SS-10 to SS-13)
└── customer/
    ├── browsing-and-search.md    (C-01 to C-06)
    ├── checkout-and-payments.md  (C-09 to C-13)
    └── orders-and-shipments.md   (C-20 to C-23)
```

## Story Index

### Customer
| ID | Title | File |
|----|-------|------|
| C-01 | Browse storefront on subdomain or custom domain | browsing-and-search.md |
| C-02 | View categories and product listing | browsing-and-search.md |
| C-03 | View product detail with variants | browsing-and-search.md |
| C-04 | Search products by keyword | browsing-and-search.md |
| C-05 | Add products to cart and see cart summary | browsing-and-search.md |
| C-06 | Get help from AI Support Agent | browsing-and-search.md |
| C-09 | Log in with phone and OTP | checkout-and-payments.md |
| C-09b | Request a new OTP or handle lockout | checkout-and-payments.md |
| C-10 | Enter shipping address and choose shipping method | checkout-and-payments.md |
| C-11 | Choose payment method and complete payment | checkout-and-payments.md |
| C-12 | Check out as guest (if store allows) | checkout-and-payments.md |
| C-13 | Log in with phone+OTP during checkout | checkout-and-payments.md |
| C-20 | View my order history | orders-and-shipments.md |
| C-21 | View order detail and status | orders-and-shipments.md |
| C-22 | Track my shipment | orders-and-shipments.md |
| C-23 | Receive order and shipping notifications | orders-and-shipments.md |

### Store Owner
| ID | Title | File |
|----|-------|------|
| SO-01 | Sign up as a store owner | onboarding-and-setup.md |
| SO-02 | Create first store with username (subdomain) | onboarding-and-setup.md |
| SO-03 | Log in to store dashboard | onboarding-and-setup.md |
| SO-04 | Invite staff and assign roles | onboarding-and-setup.md |
| SO-05 | Set store basics (timezone, currency, guest checkout) | onboarding-and-setup.md |
| SO-06 | Complete AI-assisted onboarding wizard | onboarding-and-setup.md |
| SO-07 | Generate brand identity with AI | onboarding-and-setup.md |
| SO-10 | Create and manage categories | catalog-management.md |
| SO-11 | Create a product with basic info and media | catalog-management.md |
| SO-12 | Add variants to a product | catalog-management.md |
| SO-13 | Manage stock and low-stock alerts | catalog-management.md |
| SO-14 | Bulk edit products or variants | catalog-management.md |
| SO-15 | Reorder and replace product images | catalog-management.md |
| SO-16 | Create product listing from photo (Vision-to-Listing) | catalog-management.md |
| SO-17 | Auto-generate SEO content for products | catalog-management.md |
| SO-18 | Use AI content calendar for campaigns | catalog-management.md |
| SO-20 | View and filter orders | orders-and-fulfillment.md |
| SO-21 | Update order status through lifecycle | orders-and-fulfillment.md |
| SO-22 | Create a shipment using platform shipping | orders-and-fulfillment.md |
| SO-23 | Issue full or partial refund | orders-and-fulfillment.md |
| SO-24 | Cancel an order before fulfillment | orders-and-fulfillment.md |
| SO-30 | View store ledger and journals | accounting-and-reports.md |
| SO-31 | View revenue and expense summary | accounting-and-reports.md |
| SO-32 | View balance and request payout | accounting-and-reports.md |
| SO-33 | Export accounting or order report | accounting-and-reports.md |
| SO-34 | Scan and record expense invoices (OCR) | accounting-and-reports.md |
| SO-35 | View financial health dashboard | accounting-and-reports.md |
| SO-36 | Receive AI CFO agent reports and alerts | accounting-and-reports.md |
| SO-40 | See store subdomain | domains-and-branding.md |
| SO-41 | Add and verify a custom domain | domains-and-branding.md |
| SO-42 | See SSL status for custom domain | domains-and-branding.md |
| SO-43 | Set store branding (logo, colors, basic theme) | domains-and-branding.md |
| SO-44 | Choose and customize a theme preset | domains-and-branding.md |
| SO-45 | Customize design tokens and brand overrides | domains-and-branding.md |
| SO-46 | Edit storefront layout with drag-and-drop block editor | domains-and-branding.md |
| SO-47 | Receive AI CRO optimization suggestions | domains-and-branding.md |
| SO-48 | Apply custom CSS to storefront | domains-and-branding.md |
| SO-50 | Create and manage multiple warehouses | warehouse-management.md |
| SO-51 | Allocate inventory across warehouses | warehouse-management.md |
| SO-52 | Use smart routing for order fulfillment | warehouse-management.md |
| SO-53 | View inventory forecast and restock suggestions | warehouse-management.md |

### Store Staff
| ID | Title | File |
|----|-------|------|
| SS-01 | View orders list (according to role) | orders-and-support.md |
| SS-02 | View order detail and timeline | orders-and-support.md |
| SS-03 | Update order status (if permitted) | orders-and-support.md |
| SS-04 | Create shipment for an order | orders-and-support.md |
| SS-05 | Look up customer by phone or order number | orders-and-support.md |
| SS-10 | View products and variant stock | inventory-handling.md |
| SS-11 | Update variant stock (if permitted) | inventory-handling.md |
| SS-12 | View low-stock report | inventory-handling.md |
| SS-13 | Handle warehouse-specific stock (if permitted) | inventory-handling.md |

### Platform Admin
| ID | Title | File |
|----|-------|------|
| PA-01 | Log in to platform admin | auth-and-access.md |
| PA-02 | Enforce platform admin role | auth-and-access.md |
| PA-03 | View audit log for sensitive actions | auth-and-access.md |
| PA-04 | Use strong password policy | auth-and-access.md |
| PA-10 | Manage global platform settings | platform-config.md |
| PA-11 | Configure default store settings | platform-config.md |
| PA-12 | Manage reserved/blacklisted subdomains | platform-config.md |
| PA-13 | Configure AI service settings | platform-config.md |
| PA-14 | Manage design system and theme governance | platform-config.md |
| PA-15 | Manage SMS/Email provider configuration | platform-config.md |
| PA-20 | Enable/disable platform shipping globally | shipping-service.md |
| PA-21 | Configure shipping carriers and rates | shipping-service.md |
| PA-22 | View all shipments and delivery status | shipping-service.md |
| PA-23 | Manually update shipment status | shipping-service.md |
| PA-30 | List and search all stores | stores-and-billing.md |
| PA-31 | View store detail and key metrics | stores-and-billing.md |
| PA-32 | Suspend or reactivate a store | stores-and-billing.md |
| PA-33 | Approve/reject store payout requests | stores-and-billing.md |
| PA-34 | View platform-level commission summary | stores-and-billing.md |
| PA-35 | View platform dashboard with key KPIs | stores-and-billing.md |

## Usage

- Reference story IDs (e.g. `PA-01`, `SO-02`) in PRD, tickets, and code comments.
- Acceptance criteria should be testable (manual or automated).
- When adding new stories, keep the same format and add to the appropriate role folder.
- Stories cover both the core e-commerce platform (PRD.md) and the Design System & Theme Engine (DesignSystem-PRD.md).
