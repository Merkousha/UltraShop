# Sprint 4 — SO-50: Create default warehouse per store (migration from no-warehouse structure)

from django.db import migrations


def create_default_warehouses(apps, schema_editor):
    Store = apps.get_model("core", "Store")
    Warehouse = apps.get_model("core", "Warehouse")
    for store in Store.objects.all():
        if not Warehouse.objects.filter(store=store).exists():
            Warehouse.objects.create(
                store=store,
                name="انبار پیش‌فرض",
                is_default=True,
                is_active=True,
                priority=0,
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_warehouse_and_staff_warehouses"),
    ]

    operations = [
        migrations.RunPython(create_default_warehouses, noop),
    ]
