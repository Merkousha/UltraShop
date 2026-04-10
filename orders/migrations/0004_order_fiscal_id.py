from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_order_discount_amount_order_discount_code_used"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="fiscal_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Fiscal ID from Moadian tax system after invoice submission.",
                max_length=200,
            ),
        ),
    ]
