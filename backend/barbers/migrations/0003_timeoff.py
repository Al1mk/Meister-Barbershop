from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, Q


class Migration(migrations.Migration):

    dependencies = [
        ("barbers", "0002_barber_working_days"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeOff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("reason", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "barber",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="time_offs",
                        to="barbers.barber",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_time_offs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-start_date", "-end_date", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="timeoff",
            constraint=models.CheckConstraint(check=Q(("start_date__lte", F("end_date"))), name="timeoff_start_before_end"),
        ),
    ]
