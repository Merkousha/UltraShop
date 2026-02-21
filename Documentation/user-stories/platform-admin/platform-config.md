# Platform Admin — Platform Configuration

Stories for global platform settings, design system governance, and AI service configuration.

---

## PA-10: Manage global platform settings

**As a** PlatformAdmin  
**I want** to view and edit global platform settings (branding, support email, legal URLs)  
**So that** the platform presents a consistent identity and legal information to all users.

**Acceptance criteria:**

- "تنظیمات پلتفرم" section exists at `/platform/settings/`.
- Editable fields include: platform name, support email, terms of service URL, privacy policy URL, logo, and favicon.
- `PlatformSettings` is a singleton model; changes are saved and reflected on central pages and email footers via context processor.
- Sensitive changes are recorded in the audit log.

---

## PA-11: Configure default store settings

**As a** PlatformAdmin  
**I want** to set default values for new stores (e.g. time zone, currency, guest checkout)  
**So that** new stores start with sensible defaults and less configuration.

**Acceptance criteria:**

- Default time zone, display currency (e.g. IRR), and guest checkout default (on/off) can be configured.
- When a new store is created, these defaults are applied; store owner can override per store.
- Defaults are clearly labeled as "پیش‌فرض برای فروشگاه‌های جدید" in the UI.

---

## PA-12: Manage reserved and blacklisted subdomains

**As a** PlatformAdmin  
**I want** to manage reserved and blacklisted usernames (subdomains)  
**So that** system paths (e.g. `api`, `admin`, `www`) and inappropriate names are not used as store subdomains.

**Acceptance criteria:**

- A list of reserved/blacklisted usernames is configurable in platform admin.
- Store creation and username change validate against this list; reserved names are rejected with a clear message.
- Adding or removing entries does not require code deploy (stored in DB or editable config).

---

## PA-13: Configure AI service settings

**As a** PlatformAdmin  
**I want** to configure AI service providers and settings (model selection, API keys, feature toggles)  
**So that** AI features work correctly and costs are controlled.

**Acceptance criteria:**

- AI configuration section in platform admin covers: active AI model provider (e.g. GPT-4o, Claude), API credentials (stored encrypted), and per-feature toggles (Vision-to-Listing, SEO Automator, Brand AI, CRO Agent, CFO Agent, Support Agent).
- I can enable/disable individual AI features globally; when disabled, stores do not see the feature in their dashboard.
- Usage limits can be set (e.g. max AI requests per store per day) to control costs.
- AI configuration changes are recorded in audit log.
- API credentials are never displayed in full after saving; only a masked preview (e.g. `sk-...abc`).

---

## PA-14: Manage design system and theme governance

**As a** PlatformAdmin  
**I want** to manage theme presets, design tokens, and the theme versioning policy  
**So that** all stores have access to quality themes and visual consistency is maintained.

**Acceptance criteria:**

- "سیستم طراحی" (Design System) section in platform admin lists all available theme presets with version numbers.
- I can add, edit, or deprecate theme presets; deprecation shows a warning to stores using that preset and offers a migration path.
- Global design tokens (color scales, typography scales, spacing/radius/shadow scales, motion definitions) are viewable and editable at the platform level.
- Breaking changes to tokens require a deprecation window; no token is renamed without a fallback in the current version.
- Theme versioning: each theme has a version number; stores can preview before upgrading to a new theme engine version.
- CSS performance budget (< 50kb gzipped per store) is monitored; themes exceeding the budget are flagged.
- Accessibility standards (WCAG 2.1 AA minimum) are enforced; presets are validated for contrast and focus states.

---

## PA-15: Manage SMS/Email provider configuration

**As a** PlatformAdmin  
**I want** to configure the SMS and email providers used by the platform  
**So that** OTP delivery, order notifications, and transactional emails work correctly.

**Acceptance criteria:**

- SMS provider configuration: select provider (e.g. Kavenegar, mock), API credentials (encrypted), sender number.
- Email provider configuration: SMTP settings or provider API, `DEFAULT_FROM_EMAIL`, reply-to address.
- I can test the configuration by sending a test SMS or email from the settings page.
- Provider change is applied platform-wide; individual stores may override the "from" name but not the provider.
- Configuration changes are recorded in audit log.
