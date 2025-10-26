import base64
from datetime import date, datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from barbers.models import Barber, TimeOff
from bookings.models import Appointment, Customer, SALON_TIME_ZONE
from bookings.views import AppointmentViewSet, _collect_time_off_dates, _generate_daily_slots


def _future_datetime(days_ahead: int, hour: int = 10, minute: int = 0) -> datetime:
    target_date = timezone.localdate() + timedelta(days=days_ahead)
    naive = datetime.combine(target_date, time(hour=hour, minute=minute))
    return timezone.make_aware(naive, SALON_TIME_ZONE)


class TimeOffModelTests(APITestCase):
    def setUp(self):
        self.barber = Barber.objects.create(name="Tester")

    def test_prevent_overlapping_time_off(self):
        TimeOff.objects.create(barber=self.barber, start_date=date(2025, 10, 1), end_date=date(2025, 10, 3))
        with self.assertRaises(ValidationError):
            TimeOff.objects.create(barber=self.barber, start_date=date(2025, 10, 2), end_date=date(2025, 10, 4))


@override_settings(BASIC_ADMIN_PASSWORD="topsecret")
class TimeOffApiTests(APITestCase):
    def setUp(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Basic {base64.b64encode(b'admin:topsecret').decode()}"
        )
        self.barber = Barber.objects.create(name="ApiTester")
        self.customer = Customer.objects.create(name="Customer", email="cust@example.com", phone="123456789")

    def _book_appointment(self, days_ahead: int = 5):
        start_at = _future_datetime(days_ahead)
        Appointment.objects.create(
            barber=self.barber,
            customer=self.customer,
            start_at=start_at,
            duration_minutes=30,
            service_type="haircut",
        )

    def test_conflicts_endpoint_lists_appointments(self):
        self._book_appointment()
        start_date = (timezone.localdate() + timedelta(days=5)).isoformat()
        end_date = start_date

        response = self.client.get(
            "/api/admin/timeoff/conflicts",
            {
                "barber_id": self.barber.id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["appointments"]), 1)

    def test_force_creation_cancels_appointments(self):
        self._book_appointment(days_ahead=4)
        target_date = timezone.localdate() + timedelta(days=4)

        response = self.client.post(
            f"/api/admin/barbers/{self.barber.id}/timeoff",
            {
                "start_date": target_date.isoformat(),
                "end_date": target_date.isoformat(),
                "reason": "Vacation",
                "force": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        response = self.client.post(
            f"/api/admin/barbers/{self.barber.id}/timeoff",
            {
                "start_date": target_date.isoformat(),
                "end_date": target_date.isoformat(),
                "reason": "Vacation",
                "force": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TimeOff.objects.filter(barber=self.barber).exists())
        appointment = Appointment.objects.get(barber=self.barber)
        self.assertEqual(appointment.status, "cancelled")
        self.assertEqual(appointment.cancel_reason, "Admin time-off")

    def test_blocked_days_not_available(self):
        start_date = timezone.localdate() + timedelta(days=3)
        TimeOff.objects.create(barber=self.barber, start_date=start_date, end_date=start_date)

        blocked = _collect_time_off_dates(self.barber, start_date, start_date)
        self.assertIn(start_date, blocked)

        slots = _generate_daily_slots(self.barber, start_date, 30, existing=None, blocked_dates=blocked)
        self.assertEqual(slots, [])

        start_dt = timezone.make_aware(datetime.combine(start_date, time(hour=10, minute=0)), SALON_TIME_ZONE)
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                barber=self.barber,
                customer=self.customer,
                start_at=start_dt,
                duration_minutes=30,
                service_type="haircut",
            )
