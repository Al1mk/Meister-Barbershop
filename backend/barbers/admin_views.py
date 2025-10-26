from __future__ import annotations

import base64
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Appointment, SALON_TIME_ZONE

from .models import Barber, TimeOff
from .serializers import TimeOffCreateSerializer, TimeOffSerializer


class BasicAdminPasswordPermission(BasePermission):
    message = "Authentication required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and user.is_staff:
            return True

        expected = getattr(settings, "BASIC_ADMIN_PASSWORD", "")
        if not expected:
            return False

        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Basic "):
            return False

        token = header.split(" ", 1)[1]
        try:
            decoded = base64.b64decode(token).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False

        if ":" not in decoded:
            return False

        _, provided_password = decoded.split(":", 1)
        return provided_password == expected


def _collect_conflicts(barber: Barber, start_date: date, end_date: date):
    time_off_qs = TimeOff.objects.filter(barber=barber, start_date__lte=end_date, end_date__gte=start_date).order_by("start_date")
    appointment_qs = (
        Appointment.objects.exclude(status="cancelled")
        .filter(barber=barber, start_at__date__gte=start_date, start_at__date__lte=end_date)
        .select_related("customer")
        .order_by("start_at")
    )
    return time_off_qs, appointment_qs


def _serialize_conflicts(time_off_qs, appointment_qs):
    return {
        "time_off": TimeOffSerializer(time_off_qs, many=True).data,
        "appointments": [
            {
                "id": appt.id,
                "start_at": timezone.localtime(appt.start_at, SALON_TIME_ZONE).isoformat(),
                "end_at": timezone.localtime(appt.end_at, SALON_TIME_ZONE).isoformat(),
                "customer": {
                    "id": appt.customer_id,
                    "name": appt.customer.name,
                    "phone": appt.customer.phone,
                },
                "status": appt.status,
            }
            for appt in appointment_qs
        ],
    }


class BarberTimeOffView(APIView):
    authentication_classes: tuple = ()
    permission_classes = [BasicAdminPasswordPermission]

    def get(self, request, barber_id: int):
        barber = get_object_or_404(Barber, pk=barber_id)
        queryset = barber.time_offs.order_by("start_date")
        serializer = TimeOffSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, barber_id: int):
        barber = get_object_or_404(Barber, pk=barber_id)
        serializer = TimeOffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        start_date = payload["start_date"]
        end_date = payload["end_date"]
        reason = payload.get("reason", "")
        force = payload.get("force", False)

        time_off_conflicts, appointment_conflicts = _collect_conflicts(barber, start_date, end_date)

        if time_off_conflicts.exists():
            conflicts = _serialize_conflicts(time_off_conflicts, appointment_conflicts)
            return Response({"detail": "Existing time-off overlaps.", "conflicts": conflicts}, status=status.HTTP_409_CONFLICT)

        if appointment_conflicts.exists() and not force:
            conflicts = _serialize_conflicts([], appointment_conflicts)
            return Response({"detail": "Conflicts detected.", "conflicts": conflicts}, status=status.HTTP_409_CONFLICT)

        instance = TimeOff(barber=barber, start_date=start_date, end_date=end_date, reason=reason or "")
        if request.user and request.user.is_authenticated:
            instance.created_by = request.user
        try:
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

        if force and appointment_conflicts.exists():
            Appointment.objects.filter(pk__in=[appt.pk for appt in appointment_conflicts]).update(
                status="cancelled", cancel_reason="Admin time-off"
            )

        response_data = TimeOffSerializer(instance).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class TimeOffDetailView(APIView):
    authentication_classes: tuple = ()
    permission_classes = [BasicAdminPasswordPermission]

    def delete(self, request, pk: int):
        instance = get_object_or_404(TimeOff, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimeOffConflictsView(APIView):
    authentication_classes: tuple = ()
    permission_classes = [BasicAdminPasswordPermission]

    def get(self, request):
        barber_id = request.query_params.get("barber_id")
        start_raw = request.query_params.get("start_date")
        end_raw = request.query_params.get("end_date")

        if not barber_id or not start_raw or not end_raw:
            raise DRFValidationError({"detail": "barber_id، start_date و end_date الزامی است."})

        barber = get_object_or_404(Barber, pk=barber_id)

        try:
            start_date = date.fromisoformat(start_raw)
            end_date = date.fromisoformat(end_raw)
        except ValueError as exc:
            raise DRFValidationError({"detail": "فرمت تاریخ اشتباه است. 2025-10-01"}) from exc

        if end_date < start_date:
            raise DRFValidationError({"detail": "start_date باید قبل از end_date باشد."})

        time_off_conflicts, appointment_conflicts = _collect_conflicts(barber, start_date, end_date)
        return Response(_serialize_conflicts(time_off_conflicts, appointment_conflicts))
