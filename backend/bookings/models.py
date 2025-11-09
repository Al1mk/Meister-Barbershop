from __future__ import annotations

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from barbers.models import Barber, TimeOff

SALON_TIME_ZONE = ZoneInfo(getattr(settings, "TIME_ZONE", "Europe/Berlin"))

OPEN_WEEKDAYS = {0, 1, 2, 3, 4, 5}  # Monday..Saturday
REZA_WEEKDAYS = {4, 5}  # Friday & Saturday
REZA_ALIASES = {"reza", "رضا"}

START_OF_DAY = time(hour=9, minute=30)
LAST_APPOINTMENT_END = time(hour=18, minute=30)
MAX_START_TIME = time(hour=18, minute=0)

SLOT_STEP_MINUTES = 10

SERVICE_CHOICES = (
    ("haircut", "haircut"),
    ("hair_beard", "hair_beard"),
)

SERVICE_DURATION_MAP = {
    "haircut": 30,
    "hair_beard": 45,
}

DEFAULT_DURATION_MINUTES = SERVICE_DURATION_MAP["haircut"]


def _normalize_barber_name(barber: Barber | None) -> str:
    name = (barber.name or "") if barber else ""
    return name.strip()


def allowed_weekdays_for_barber(barber: Barber | None) -> set[int]:
    name = _normalize_barber_name(barber)
    if name:
        lowered = name.casefold()
        if lowered in REZA_ALIASES or name == "رضا":
            return REZA_WEEKDAYS
    return OPEN_WEEKDAYS


def _to_minutes(value: int | str | None) -> int | None:
    if value in (None, "", "null"):
        return None
    try:
        int_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("مدت سرویس نامعتبر است.") from exc
    return int_value


class Customer(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("email", "phone")

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class Appointment(models.Model):
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, related_name="appointments")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="appointments")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(editable=False)
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, blank=True)
    duration_minutes = models.PositiveIntegerField(default=DEFAULT_DURATION_MINUTES)
    status = models.CharField(
        max_length=10,
        choices=[("booked", "booked"), ("completed", "completed"), ("cancelled", "cancelled")],
        default="booked",
    )
    cancel_reason = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    review_requested = models.BooleanField(default=False)
    review_request_sent_at = models.DateTimeField(null=True, blank=True)

    # Follow-up email tracking (2-hour post-appointment review request)
    followup_sent = models.BooleanField(default=False)
    followup_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("barber", "start_at")

    SERVICE_TYPE_CHOICES = SERVICE_CHOICES

    @classmethod
    def normalize_service_meta(cls, service_type: str | None, duration_minutes: int | str | None) -> tuple[str | None, int]:
        normalized_type: str | None = None
        resolved_duration: int | None = None

        if service_type:
            candidate = service_type.strip().lower()
            if candidate not in SERVICE_DURATION_MAP:
                raise ValidationError("نوع سرویس نامعتبر است.")
            normalized_type = candidate
            resolved_duration = SERVICE_DURATION_MAP[candidate]

        provided_duration = _to_minutes(duration_minutes)
        if provided_duration is not None:
            if provided_duration <= 0:
                raise ValidationError("مدت سرویس باید بزرگتر از صفر باشد.")
            if resolved_duration is not None and provided_duration != resolved_duration:
                raise ValidationError("مدت سرویس با نوع انتخاب‌شده هم‌خوانی ندارد.")
            resolved_duration = provided_duration

        if resolved_duration is None:
            raise ValidationError("مدت سرویس مشخص نشده است.")

        return normalized_type, resolved_duration

    def clean(self):
        if not self.start_at:
            raise ValidationError("زمان شروع الزامی است.")

        normalized_type, duration = self.normalize_service_meta(
            getattr(self, "service_type", None),
            getattr(self, "duration_minutes", None),
        )

        start_at = self.start_at
        if timezone.is_naive(start_at):
            start_local = timezone.make_aware(start_at, SALON_TIME_ZONE)
        else:
            start_local = timezone.localtime(start_at, SALON_TIME_ZONE)

        today_local = timezone.localdate()
        if start_local.date() <= today_local:
            raise ValidationError("امکان رزرو برای امروز یا گذشته وجود ندارد.")

        weekday = start_local.weekday()
        if weekday == 6:
            raise ValidationError("یکشنبه‌ها سالن تعطیل است.")

        barber = getattr(self, "barber", None)
        if barber:
            allowed_days = allowed_weekdays_for_barber(barber)
            if weekday not in allowed_days:
                raise ValidationError("این آرایشگر در روز انتخاب‌شده کار نمی‌کند.")

            if TimeOff.objects.filter(
                barber=barber,
                start_date__lte=start_local.date(),
                end_date__gte=start_local.date(),
            ).exists():
                raise ValidationError("این تاریخ برای آرایشگر مسدود شده است.")

        slot_start_time = start_local.time().replace(second=0, microsecond=0)
        if start_local.second != 0 or start_local.microsecond != 0:
            raise ValidationError("رزرو باید سرِ دقیقه انجام شود.")

        if slot_start_time < START_OF_DAY:
            raise ValidationError("ساعت انتخابی خارج از ساعات کاری سالن است.")

        if slot_start_time >= MAX_START_TIME:
            raise ValidationError("شروع نوبت پس از ۱۸:۰۰ مجاز نیست.")

        closing_dt = timezone.make_aware(datetime.combine(start_local.date(), LAST_APPOINTMENT_END), SALON_TIME_ZONE)

        slot_end = start_local + timedelta(minutes=duration)
        if slot_end > closing_dt:
            raise ValidationError("ساعت انتخابی خارج از ساعات کاری سالن است.")

        conflict_qs = (
            Appointment.objects.exclude(pk=self.pk)
            .exclude(status="cancelled")
            .filter(barber=self.barber, start_at__date=start_local.date())
        )

        for other in conflict_qs:
            other_start = timezone.localtime(other.start_at, SALON_TIME_ZONE)
            other_end = timezone.localtime(other.end_at, SALON_TIME_ZONE)
            if other_start < slot_end and other_end > start_local:
                raise ValidationError("این بازه قبلاً رزرو شده است.")

        self.service_type = normalized_type or ""
        self.duration_minutes = duration
        self.start_at = start_local
        self.end_at = slot_end

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status != "cancelled":
            self.cancel_reason = ""
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.barber.name} @ {self.start_at.isoformat()}"


class Notification(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=[("confirmation", "confirmation"), ("review", "review")])
    channel = models.CharField(max_length=10, choices=[("email", "email"), ("sms", "sms")])
    sent_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[("success", "success"), ("failed", "failed")])
    details = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("appointment", "type", "channel")
