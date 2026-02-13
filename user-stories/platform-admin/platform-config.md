# Platform Admin — Platform Configuration

Stories for global platform settings and configuration.

**Implementation:** PA-10: `core.PlatformSettings` (singleton) with name, support_email, terms_url, privacy_url, logo, favicon. Edit at `/platform/settings/`. Context processor exposes `platform_settings` to templates; base template uses it for title, header, and footer (terms, privacy, support links).

---

## PA-10: Manage global platform settings

**As a** PlatformAdmin  
**I want** to view and edit global platform settings (branding, support email, legal URLs)  
**So that** the platform presents a consistent identity and legal information to all users.

**Acceptance criteria:**

- A "Platform settings" or "Global config" section exists in platform admin.
- Editable fields include: platform name, support email, terms of service URL, privacy policy URL, and optional logo/favicon.
- Changes are saved and reflected on the central marketing/landing pages and in emails (e.g. footer links).
- Sensitive changes (if any) are recorded in the audit log.

---

## PA-11: Configure default store settings

**As a** PlatformAdmin  
**I want** to set default values for new stores (e.g. time zone, currency, guest checkout)  
**So that** new stores start with sensible defaults and less configuration.

**Acceptance criteria:**

- Default time zone, display currency (e.g. IRR), and guest checkout default (on/off) can be configured.
- When a new store is created, these defaults are applied; store owner can override per store.
- Defaults are clearly labeled as "default for new stores" in the UI.

---

## PA-12: Manage reserved and blacklisted subdomains

**As a** PlatformAdmin  
**I want** to manage reserved and blacklisted usernames (subdomains)  
**So that** system paths (e.g. `api`, `admin`, `www`) and inappropriate names are not used as store subdomains.

**Acceptance criteria:**

- A list of reserved/blacklisted usernames is configurable (e.g. `api`, `admin`, `www`, `mail`, `ftp`).
- Store creation and username change validate against this list; reserved names are rejected with a clear message.
- Adding or removing entries does not require code deploy (stored in DB or config that platform admin can edit).
