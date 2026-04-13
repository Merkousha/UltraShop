from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0002_chatsession_chatmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="saletask",
            name="overdue_reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="saletask",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="contactactivity",
            name="activity_type",
            field=models.CharField(
                choices=[
                    ("order", "سفارش"),
                    ("note", "یادداشت"),
                    ("call", "تماس"),
                    ("email", "ایمیل"),
                    ("chat", "چت"),
                    ("ticket", "تیکت پشتیبانی"),
                ],
                max_length=10,
            ),
        ),
    ]
