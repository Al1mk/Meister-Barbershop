from __future__ import annotations

from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from barbers.models import Barber

from .models import (
    Appointment,
    LAST_APPOINTMENT_END,
    MAX_START_TIME,
    SALON_TIME_ZONE,
    SLOT_STEP_MINUTES,
    START_OF_DAY,
    allowed_weekdays_for_barber,
)
from .serializers import AppointmentCreateSerializer, AppointmentOutSerializer


SLOT_STEP_DELTA = timedelta(minutes=SLOT_STEP_MINUTES)


def _parse_date(value: str | None) -> date:
    if not value:
        raise DRFValidationError({"date": "تاریخ ارسال نشده است."})
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DRFValidationError({"date": "فرمت تاریخ اشتباه است. 2025-10-01"}) from exc


def _resolve_service_from_request(service_type: str | None, duration_raw: str | None) -> tuple[str | None, int]:
    if duration_raw in ("", None):
        duration_value = None
    else:
        try:
            duration_value = int(duration_raw)
        except (TypeError, ValueError) as exc:
            raise DRFValidationError({"duration_minutes": "مدت سرویس نامعتبر است."}) from exc

    try:
        return Appointment.normalize_service_meta(service_type, duration_value)
    except DjangoValidationError as exc:
        raise DRFValidationError(exc.messages) from exc


def _collect_bookings(barber: Barber, start_date: date, end_date: date) -> dict[date, list[tuple[datetime, datetime]]]:
    qs = (
        Appointment.objects.exclude(status="cancelled")
        .filter(barber=barber, start_at__date__gte=start_date, start_at__date__lte=end_date)
        .order_by("start_at")
    )
    bookings: dict[date, list[tuple[datetime, datetime]]] = {}
    for appt in qs:
        local_start = timezone.localtime(appt.start_at, SALON_TIME_ZONE)
        local_end = timezone.localtime(appt.end_at, SALON_TIME_ZONE)
        bookings.setdefault(local_start.date(), []).append((local_start, local_end))
    return bookings


def _generate_daily_slots(
    barber: Barber,
    target_date: date,
    duration_minutes: int,
    existing: list[tuple[datetime, datetime]] | None = None,
) -> list[datetime]:
    today_local = timezone.localdate()
    if target_date <= today_local:
        return []

    weekday = target_date.weekday()
    if weekday == 6:
        return []

    allowed_days = allowed_weekdays_for_barber(barber)
    if weekday not in allowed_days:
        return []

    duration_delta = timedelta(minutes=duration_minutes)
    start_dt = timezone.make_aware(datetime.combine(target_date, START_OF_DAY), SALON_TIME_ZONE)
    closing_dt = timezone.make_aware(datetime.combine(target_date, LAST_APPOINTMENT_END), SALON_TIME_ZONE)
    max_start_dt = timezone.make_aware(datetime.combine(target_date, MAX_START_TIME), SALON_TIME_ZONE)

    windows = sorted(existing or [], key=lambda chunk: chunk[0])

    slots: list[datetime] = []
    current = start_dt
    while current + duration_delta <= closing_dt:
        if current >= max_start_dt:
            break
        candidate_end = current + duration_delta
        conflict = any(existing_start < candidate_end and existing_end > current for existing_start, existing_end in windows)
        if not conflict:
            slots.append(current)
        current += SLOT_STEP_DELTA

    return slots


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related("barber", "customer").all().order_by("-start_at")
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_serializer_class(self):
        return AppointmentCreateSerializer if self.action == "create" else AppointmentOutSerializer

    @action(detail=False, methods=["get"], url_path="slots")
    def slots(self, request):
        barber_id = request.query_params.get("barber_id")
        date_str = request.query_params.get("date")
        service_type = request.query_params.get("service_type")
        duration_raw = request.query_params.get("duration_minutes")

        if not barber_id:
            return Response({"detail": "barber_id لازم است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            barber = Barber.objects.get(pk=barber_id, is_active=True)
        except Barber.DoesNotExist:
            return Response({"detail": "آرایشگر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        target_date = _parse_date(date_str)
        normalized_type, duration_minutes = _resolve_service_from_request(service_type, duration_raw)

        bookings = _collect_bookings(barber, target_date, target_date)
        slots = _generate_daily_slots(barber, target_date, duration_minutes, bookings.get(target_date))
        payload = {
            "date": target_date.isoformat(),
            "barber": barber.id,
            "service_type": normalized_type,
            "duration_minutes": duration_minutes,
            "slots": [slot.astimezone(SALON_TIME_ZONE).strftime("%H:%M") for slot in slots],
        }
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="availability")
    def availability(self, request):
        barber_id = request.query_params.get("barber_id")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")
        service_type = request.query_params.get("service_type")
        duration_raw = request.query_params.get("duration_minutes")

        if not barber_id or not start_str or not end_str:
            return Response({"detail": "barber_id، start و end لازم است."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            barber = Barber.objects.get(pk=barber_id, is_active=True)
        except Barber.DoesNotExist:
            return Response({"detail": "آرایشگر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        try:
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
        except ValueError:
            return Response({"detail": "فرمت تاریخ اشتباه است. 2025-10-01"}, status=status.HTTP_400_BAD_REQUEST)

        if end_date < start_date:
            return Response({"detail": "start باید قبل از end باشد."}, status=status.HTTP_400_BAD_REQUEST)

        if (end_date - start_date).days > 62:
            return Response({"detail": "بازه زمانی حداکثر باید ۲ ماه باشد."}, status=status.HTTP_400_BAD_REQUEST)

        normalized_type, duration_minutes = _resolve_service_from_request(service_type, duration_raw)

        bookings = _collect_bookings(barber, start_date, end_date)

        days = []
        current = start_date
        while current <= end_date:
            possible_slots = _generate_daily_slots(barber, current, duration_minutes, [])
            free_slots = _generate_daily_slots(barber, current, duration_minutes, bookings.get(current))
            days.append(
                {
                    "date": current.isoformat(),
                    "free": len(free_slots),
                    "total": len(possible_slots),
                }
            )
            current += timedelta(days=1)

        return Response(
            {
                "barber": barber.id,
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "service_type": normalized_type,
                "duration_minutes": duration_minutes,
                "days": days,
            }
        )

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().create(request, *args, **kwargs)
