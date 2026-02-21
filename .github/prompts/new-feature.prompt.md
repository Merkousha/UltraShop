---
description: "Create a new Django app or add a new feature module to UltraShop following existing patterns."
agent: "django-developer"
argument-hint: "Feature description (e.g., 'customer cart and checkout')"
---
Create the requested feature for UltraShop:

1. Read relevant user stories from `Documentation/user-stories/` and PRD from `Documentation/PRD.md`
2. Study existing patterns: read models, views, and templates from similar apps
3. Create/update models with proper multi-tenancy (`store` FK), IRR currency fields, and timestamps
4. Create views with appropriate access mixins (`StoreAccessMixin`, `PlatformAdminMixin`, or `StoreMixin`)
5. Register URLs with proper namespacing
6. Create templates extending the correct base, using local static assets and Persian text
7. Run `python manage.py makemigrations && python manage.py migrate`
8. Run `python manage.py check` to verify

Follow the existing code style exactly — CBVs, request.POST processing, Tailwind styling.
