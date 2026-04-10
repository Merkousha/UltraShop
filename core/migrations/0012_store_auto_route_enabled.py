from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_store_notification_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="auto_route_enabled",
            field=models.BooleanField(
                default=False,
                help_text="If True, automatically compute and apply smart routing when an order is paid.",
            ),
        ),
    ]
