from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from core.models import PlatformSettings, User


class Command(BaseCommand):
    help = "Seed initial platform data: PlatformAdmin group, PlatformSettings, superuser"

    def handle(self, *args, **options):
        # 1. Create PlatformAdmin group
        group, created = Group.objects.get_or_create(name="PlatformAdmin")
        if created:
            self.stdout.write(self.style.SUCCESS("Created PlatformAdmin group"))
        else:
            self.stdout.write("PlatformAdmin group already exists")

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
            group.user_set.add(user)
            self.stdout.write(self.style.SUCCESS(
                f"Created superuser: {email} / Admin@12345"
            ))
        else:
            self.stdout.write(f"Superuser {email} already exists")

        # 4. Seed theme presets
        from django.core.management import call_command
        call_command("seed_theme_presets")

        self.stdout.write(self.style.SUCCESS("Seed complete!"))
