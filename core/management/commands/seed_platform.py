from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from core.models import PlatformSettings, StorePlan, User


class Command(BaseCommand):
    help = "Seed initial platform data: PlatformAdmin group, PlatformSettings, superuser, plans"

    def handle(self, *args, **options):
        # 1. Create platform roles
        platform_admin_group, created = Group.objects.get_or_create(name="PlatformAdmin")
        if created:
            self.stdout.write(self.style.SUCCESS("Created PlatformAdmin group"))
        else:
            self.stdout.write("PlatformAdmin group already exists")

        super_admin_group, created = Group.objects.get_or_create(name="SuperAdmin")
        if created:
            self.stdout.write(self.style.SUCCESS("Created SuperAdmin group"))
        else:
            self.stdout.write("SuperAdmin group already exists")

        # 2. Initialize PlatformSettings
        ps = PlatformSettings.load()
        if not ps.reserved_usernames:
            ps.reserved_usernames = [
                "api", "admin", "www", "mail", "ftp",
                "platform", "static", "media", "dashboard",
                "accounts", "login", "signup", "register",
            ]
            ps.save()
            self.stdout.write(self.style.SUCCESS("Seeded reserved usernames"))
        else:
            self.stdout.write("PlatformSettings already has reserved usernames")

        # 3. Create superuser if not exists
        email = "admin@ultra-shop.com"
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_superuser(
                username="admin",
                email=email,
                password="Admin@12345",
            )
            platform_admin_group.user_set.add(user)
            super_admin_group.user_set.add(user)
            self.stdout.write(self.style.SUCCESS(
                f"Created superuser: {email} / Admin@12345"
            ))
        else:
            self.stdout.write(f"Superuser {email} already exists")

        # 4. Seed theme presets
        from django.core.management import call_command
        call_command("seed_theme_presets")

        # 5. Seed default store plans
        plans_data = [
            {
                "slug": "starter",
                "name": "استارتر",
                "max_warehouses": 1,
                "max_products": 100,
                "max_ai_requests_daily": 10,
                "allow_custom_domain": False,
            },
            {
                "slug": "growth",
                "name": "رشد",
                "max_warehouses": 3,
                "max_products": 500,
                "max_ai_requests_daily": 50,
                "allow_custom_domain": False,
            },
            {
                "slug": "pro",
                "name": "حرفه‌ای",
                "max_warehouses": 0,   # 0 = unlimited
                "max_products": 0,     # 0 = unlimited
                "max_ai_requests_daily": 0,  # 0 = unlimited
                "allow_custom_domain": True,
            },
        ]
        for pdata in plans_data:
            slug = pdata.pop("slug")
            plan, created = StorePlan.objects.get_or_create(slug=slug, defaults=pdata)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(f"Plan already exists: {plan.name}")

        self.stdout.write(self.style.SUCCESS("Seed complete!"))
