from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0002_appointment_duration_minutes_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="cancel_reason",
            field=models.CharField(blank=True, default="", max_length=120),
            preserve_default=False,
        ),
    ]
