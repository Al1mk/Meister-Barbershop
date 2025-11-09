"""
Unit tests for follow-up email functionality.
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from io import StringIO

from bookings.models import Appointment, Customer, FollowUpRequest
from barbers.models import Barber


class FollowUpEmailTestCase(TestCase):
    """Test follow-up email sending logic."""

    def setUp(self):
        """Set up test data."""
        self.barber = Barber.objects.create(name="Test Barber", email="barber@test.com")
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="customer@test.com",
            phone="+491234567890"
        )

    def test_dry_run_does_not_send_emails(self):
        """Test that dry-run mode does not send emails or create records."""
        # Create appointment eligible for follow-up
        appt = Appointment.objects.create(
            barber=self.barber,
            customer=self.customer,
            start_at=timezone.now() + timedelta(days=1, hours=10),
            end_at=timezone.now() + timedelta(days=1, hours=10, minutes=30),
            service_type="haircut",
            duration_minutes=30,
            status="booked",
        )
        # Backdate creation time to make it eligible
        Appointment.objects.filter(pk=appt.pk).update(
            created_at=timezone.now() - timedelta(hours=3)
        )

        # Run dry-run
        out = StringIO()
        call_command('send_followups', '--dry-run', stdout=out)
        output = out.getvalue()

        # Verify no FollowUpRequest created
        self.assertEqual(FollowUpRequest.objects.count(), 0)

        # Verify appointment not marked as sent
        appt.refresh_from_db()
        self.assertFalse(appt.followup_sent)

        # Verify output mentions dry-run
        self.assertIn('DRY RUN', output)

    def test_single_followup_per_email(self):
        """Test that each email receives only one follow-up."""
        # Create FollowUpRequest
        FollowUpRequest.objects.create(
            email="customer@test.com",
            appointment=None,
        )

        # Create appointment for same email
        appt = Appointment.objects.create(
            barber=self.barber,
            customer=self.customer,
            start_at=timezone.now() + timedelta(days=1, hours=10),
            end_at=timezone.now() + timedelta(days=1, hours=10, minutes=30),
            service_type="haircut",
            duration_minutes=30,
            status="booked",
        )
        Appointment.objects.filter(pk=appt.pk).update(
            created_at=timezone.now() - timedelta(hours=3)
        )

        # Run command (dry-run to avoid actual email sending)
        out = StringIO()
        call_command('send_followups', '--dry-run', stdout=out)
        output = out.getvalue()

        # Should find no appointments (email already has follow-up)
        self.assertIn('No appointments eligible', output)

    def test_opt_out_prevents_followup(self):
        """Test that opted-out emails don't receive follow-ups."""
        # Create opted-out FollowUpRequest
        FollowUpRequest.objects.create(
            email="customer@test.com",
            opt_out=True,
            opted_out_at=timezone.now()
        )

        # Create appointment
        appt = Appointment.objects.create(
            barber=self.barber,
            customer=self.customer,
            start_at=timezone.now() + timedelta(days=1, hours=10),
            end_at=timezone.now() + timedelta(days=1, hours=10, minutes=30),
            service_type="haircut",
            duration_minutes=30,
            status="booked",
        )
        Appointment.objects.filter(pk=appt.pk).update(
            created_at=timezone.now() - timedelta(hours=3)
        )

        # Run command (dry-run)
        out = StringIO()
        call_command('send_followups', '--dry-run', stdout=out)
        output = out.getvalue()

        # Should find no appointments
        self.assertIn('No appointments eligible', output)
