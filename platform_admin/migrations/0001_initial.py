# Generated migration - platform_admin has no models; this creates the PlatformAdmin group.

from django.db import migrations


def create_platform_admin_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="PlatformAdmin")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("auth", "__latest__"),
    ]

    operations = [
        migrations.RunPython(create_platform_admin_group, noop),
    ]
