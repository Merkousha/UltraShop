import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0002_abandonedcart"),
    ]

    operations = [
        migrations.AddField(
            model_name="abandonedcart",
            name="recovery_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                help_text="Unique token for cart recovery deep-link.",
            ),
        ),
    ]
