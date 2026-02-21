---
description: "Review a specific app or area of UltraShop code for security, multi-tenancy, and correctness issues."
agent: "code-reviewer"
argument-hint: "App or area to review (e.g., 'dashboard views', 'accounting services')"
---
Perform a thorough code review of the specified area:

1. Read all Python files in the target app/area
2. Check for security issues: access control, data leakage between tenants, XSS, CSRF
3. Verify multi-tenancy: all queries properly scoped to store
4. Check state machine validations (shipments, orders)
5. Verify accounting integrity if touching financial code
6. Check template correctness: namespaced URLs, static loading, no CDN references

Report findings with severity, file references, and suggested fixes.
