from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


def barber_photo_path(instance, filename):
    return f"barbers/{instance.id}/{filename}"


class Barber(models.Model):
    name = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to=barber_photo_path, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    working_days = models.CharField(
        max_length=20,
        default="0,1,2,3,4,5",
        help_text="Comma separated weekday numbers (0=Mon ... 6=Sun).",
    )

    def __str__(self):
        return self.name

    def working_days_set(self) -> set[int]:
        values = set()
        for part in self.working_days.split(","):
            part = part.strip()
            if part.isdigit():
                values.add(int(part))
        return values


class TimeOff(models.Model):
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name="time_offs")
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_time_offs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_date", "-end_date", "-id")
        constraints = [
            models.CheckConstraint(check=Q(start_date__lte=F("end_date")), name="timeoff_start_before_end"),
        ]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "end_date must be on or after start_date."})

        if not self.barber_id:
            return

        overlap_qs = (
            TimeOff.objects.filter(barber=self.barber)
            .exclude(pk=self.pk)
            .filter(start_date__lte=self.end_date, end_date__gte=self.start_date)
        )
        if overlap_qs.exists():
            raise ValidationError("این آرایشگر در این بازه از قبل بلاک شده است.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.barber} {self.start_date}->{self.end_date}"

    def contains(self, target_date):
        return self.start_date <= target_date <= self.end_date
