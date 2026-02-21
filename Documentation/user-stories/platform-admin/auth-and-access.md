# Platform Admin — Auth & Access

Stories for platform administrator authentication, authorization, and audit.

---

## PA-01: Log in to platform admin

**As a** PlatformAdmin  
**I want** to log in to the platform admin panel with my credentials  
**So that** I can manage the platform, stores, and shipping service.

**Acceptance criteria:**

- Login page is available at `/platform/login/` (or central domain admin path).
- I sign in with email and password.
- Failed login attempts are rate-limited and a generic error is shown (no disclosure of which field is wrong).
- Successful login creates a session; I am redirected to the platform admin dashboard.
- Session uses secure, HttpOnly, SameSite cookies.
- Only users in the "PlatformAdmin" group can access platform admin routes; others receive 403.

---

## PA-02: Enforce platform admin role

**As a** PlatformAdmin  
**I want** platform admin area to be restricted to users with the platform admin role  
**So that** store owners and staff cannot access platform-level settings or data.

**Acceptance criteria:**

- All platform admin views check for PlatformAdmin group membership.
- Unauthorized access returns HTTP 403 and does not expose platform admin UI.
- Store context (if any) is ignored in platform admin; no store-scoped data mixed in.

---

## PA-03: View audit log for sensitive actions

**As a** PlatformAdmin  
**I want** to view an audit log of sensitive actions (refunds, payout changes, domain changes, role changes, suspensions)  
**So that** I can investigate issues and ensure compliance.

**Acceptance criteria:**

- Audit log is available at `/platform/audit-log/` with filters by action type, date, store, and actor.
- Log entries include: timestamp, actor (user/store), action type, resource_type, resource_id, and details (e.g. old/new value).
- Actions logged: refund, payout_approved, payout_rejected, store_suspended, store_reactivated, domain changes, staff role changes, accounting adjustments, platform config changes.
- Log entries are append-only (no user-facing delete); immutable for compliance.

---

## PA-04: Use strong password policy for platform admin

**As a** PlatformAdmin  
**I want** platform admin accounts to use a strong password policy  
**So that** the platform control plane remains secure.

**Acceptance criteria:**

- Password requirements: minimum 10 characters, at least one letter, one digit, one special character.
- Password change is available at `/platform/password-change/`; form enforces the policy.
- Passwords are hashed with a secure algorithm (PBKDF2 or Argon2); never stored in plain text.
- Optional: password change required on first login or when reset by another admin.
