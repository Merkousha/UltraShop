from django.core.management.base import BaseCommand
from core.models import ThemePreset


PRESETS = [
    {
        "name": "Minimal",
        "slug": "minimal",
        "description": "سبک، هوا‌دار، فضای سفید فراوان",
        "tokens": {
            "radius": "sm", "shadow": "sm", "spacing": "relaxed", "animation": "subtle",
            "primary_color": "#6366f1",
            "typography": "minimal", "heading_scale": "tight", "component_defaults": "flat",
        },
        "version": "1.0.0",
    },
    {
        "name": "Bold Commerce",
        "slug": "bold-commerce",
        "description": "کنتراست بالا، دکمه‌های قوی، گرید محصول فشرده",
        "tokens": {
            "radius": "md", "shadow": "lg", "spacing": "compact", "animation": "bold",
            "primary_color": "#ef4444",
            "typography": "bold", "heading_scale": "expanded", "component_defaults": "elevated",
        },
        "version": "1.0.0",
    },
    {
        "name": "Elegant",
        "slug": "elegant",
        "description": "الهام‌گرفته از سریف، سایه‌های ملایم، رنگ‌های خاموش",
        "tokens": {
            "radius": "lg", "shadow": "md", "spacing": "generous", "animation": "smooth",
            "primary_color": "#8b5cf6",
            "typography": "elegant", "heading_scale": "relaxed", "component_defaults": "soft",
        },
        "version": "1.0.0",
    },
    {
        "name": "Creator",
        "slug": "creator",
        "description": "خلاقانه، گرد، بازیگوشانه",
        "tokens": {
            "radius": "full", "shadow": "md", "spacing": "balanced", "animation": "playful",
            "primary_color": "#f59e0b",
            "typography": "playful", "heading_scale": "balanced", "component_defaults": "rounded",
        },
        "version": "1.0.0",
    },
]


class Command(BaseCommand):
    help = "Seed 4 default theme presets"

    def handle(self, *args, **options):
        for data in PRESETS:
            preset, created = ThemePreset.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "tokens": data["tokens"],
                    "version": data["version"],
                    "status": ThemePreset.Status.ACTIVE,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created preset: {preset.name}"))
            else:
                self.stdout.write(f"Preset already exists: {preset.name}")

        self.stdout.write(self.style.SUCCESS("Theme presets seeded!"))
