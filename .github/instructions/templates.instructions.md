---
description: "Use when creating or editing Django HTML templates. Covers RTL, Tailwind, static files, and Persian UI conventions."
applyTo: "templates/**/*.html"
---
# Template Guidelines

## Base Templates
- `templates/base.html` — Main base (dashboard, accounts)
- `templates/storefront/base.html` — Storefront with store branding
- `templates/dashboard/base.html` — Dashboard with sidebar (extends base.html)
- `templates/platform_admin/base.html` — Platform admin layout
- `templates/home.html` — Standalone landing page (does not extend base.html)

## Required Tags
- `{% load static %}` at top of every template that uses `{% static %}` — Django does NOT inherit this from parent
- `{% url 'namespace:name' %}` for all links — never hardcode URLs

## Static Assets (ALL LOCAL — NO CDN)
- Tailwind: `{% static 'js/tailwind.js' %}`
- Vazirmatn CSS: `{% static 'css/vazirmatn.css' %}`
- SortableJS: `{% static 'js/sortable.min.js' %}`
- Fonts: `static/fonts/Vazirmatn-*.woff2`

## RTL & Persian
- `<html lang="fa" dir="rtl">`
- Font: `'Vazirmatn', Tahoma, sans-serif`
- All user-facing text in Persian
- Use `text-right` as default (RTL), `text-left` only when needed for LTR content

## Tailwind Configuration
- Extend colors: neon cyan `#00f5ff`, purple `#bb00ff`, pink `#ff006e`
- Dark backgrounds: `#0a0a0f`, `#0f0f1a`, `#161625`, `#1e1e30`
- Glass-morphism: `backdrop-filter: blur()` with semi-transparent backgrounds

## Context Variables
- `{{ platform_settings }}` — PlatformSettings singleton (available everywhere via context processor)
- `{{ user }}` — Current authenticated user
- `{{ request.current_store }}` — Current store in dashboard views
- `{{ store }}` — Store object in storefront views
