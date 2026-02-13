# Platform Admin — Auth & Access

Stories for platform administrator authentication, authorization, and audit.

**Implementation:** Platform admin panel at `/platform/`: login (PA-01) at `/platform/login/` (email+password, only users in group "PlatformAdmin"); all platform routes require group check (PA-02). Audit log (PA-03) at `/platform/audit-log/`. Password policy (PA-04): platform admins change password at `/platform/password-change/`; form enforces min 10 chars, at least one letter, one digit, one special character; Django hashes with PBKDF2.

---

## PA-01: Log in to platform admin

**As a** PlatformAdmin  
**I want** to log in to the platform admin panel with my credentials  
**So that** I can manage the platform, stores, and shipping service.

**Acceptance criteria:**

- Login page is available at a dedicated URL (e.g. `/platform/admin/` or central domain admin path).
- I can sign in with email and password.
- Failed login attempts are rate-limited and a generic error is shown.
- Successful login creates a session; I am redirected to the platform admin dashboard.
- Session uses secure, HttpOnly, SameSite cookies.
- Only users with PlatformAdmin role can access platform admin routes; others receive 403.

---

## PA-02: Enforce platform admin role

**As a** PlatformAdmin  
**I want** platform admin area to be restricted to users with the platform admin role  
**So that** store owners and staff cannot access platform-level settings or data.

**Acceptance criteria:**

- All platform admin views check for PlatformAdmin role (or equivalent permission).
- Unauthorized access returns HTTP 403 and does not expose platform admin UI.
- Store context (if any) is ignored in platform admin; no store-scoped data mixed in.

---

## PA-03: View audit log for sensitive actions

**As a** PlatformAdmin  
**I want** to view an audit log of sensitive actions (refunds, payout changes, domain changes, role changes)  
**So that** I can investigate issues and ensure compliance.

**Acceptance criteria:**

- Audit log is available in platform admin (e.g. list view with filters).
- Log entries include: timestamp, actor (user/store), action type, resource (e.g. order id, store id), and optional details (e.g. old/new value for domain).
- At least the following actions are logged: refunds, payout setting changes, custom domain add/remove/verify, store staff role changes, store owner changes, manual accounting adjustments.
- Log entries are append-only (no user-facing delete).

---

## PA-04: Use strong password policy for platform admin

**As a** PlatformAdmin  
**I want** platform admin accounts to use a strong password policy  
**So that** the platform control plane remains secure.

**Acceptance criteria:**

- Password minimum length and complexity rules are enforced (e.g. length ≥ 10, mix of character types).
- Password change is required on first login or when reset by another admin (if applicable).
- Passwords are hashed with a secure algorithm (e.g. PBKDF2 or Argon2); never stored in plain text.
