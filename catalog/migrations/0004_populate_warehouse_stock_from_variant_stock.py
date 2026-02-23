# Sprint 4 — SO-50: Populate WarehouseStock from ProductVariant.stock (default warehouse per store)

from django.db import migrations


def populate_warehouse_stock(apps, schema_editor):
    Warehouse = apps.get_model("core", "Warehouse")
    ProductVariant = apps.get_model("catalog", "ProductVariant")
    WarehouseStock = apps.get_model("catalog", "WarehouseStock")

    for variant in ProductVariant.objects.select_related("product").all():
        store = variant.product.store_id
        default_wh = Warehouse.objects.filter(store_id=store, is_default=True).first()
        if not default_wh:
            default_wh = Warehouse.objects.filter(store_id=store).first()
        if default_wh and variant.stock:
            WarehouseStock.objects.get_or_create(
                warehouse=default_wh,
                variant=variant,
                defaults={"quantity": variant.stock},
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_warehouse_stock"),
        ("core", "0005_default_warehouse_per_store"),
    ]

    operations = [
        migrations.RunPython(populate_warehouse_stock, noop),
    ]
