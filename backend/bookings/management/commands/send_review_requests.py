"""
Django management command to send review requests for completed appointments.

Usage:
    python manage.py send_review_requests

This should be run via cron every 30 minutes.
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Appointment
from bookings.notifications import send_review_request_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send review requests for appointments that ended approximately 2 hours ago'

    def handle(self, *args, **options):
        now = timezone.now()

        # Find appointments that ended 90-150 minutes ago
        # This window prevents double-sending if cron drifts
        start_window = now - timedelta(minutes=150)
        end_window = now - timedelta(minutes=90)

        self.stdout.write(
            f"Looking for appointments that ended between {start_window} and {end_window}"
        )

        # Find eligible appointments
        appointments = Appointment.objects.filter(
            end_at__gte=start_window,
            end_at__lte=end_window,
            status='booked',  # Only for completed appointments (not cancelled)
            review_requested=False,  # Haven't sent review request yet
        ).select_related('customer', 'barber')

        count = appointments.count()
        self.stdout.write(f"Found {count} appointment(s) needing review requests")

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No review requests to send"))
            return

        sent_count = 0
        error_count = 0

        for appointment in appointments:
            try:
                self.stdout.write(
                    f"Sending review request for appointment {appointment.id} "
                    f"(Customer: {appointment.customer.name}, "
                    f"Barber: {appointment.barber.name}, "
                    f"Ended: {appointment.end_at})"
                )

                email_sent, sms_sent = send_review_request_notification(appointment)

                if email_sent or sms_sent:
                    # Mark as sent
                    appointment.review_requested = True
                    appointment.review_request_sent_at = now
                    appointment.save(update_fields=['review_requested', 'review_request_sent_at'])
                    sent_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Review request sent for appointment {appointment.id} "
                            f"(Email: {email_sent}, SMS: {sms_sent})"
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠ Failed to send review request for appointment {appointment.id}"
                        )
                    )

            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error processing review request for appointment {appointment.id}: {str(e)}",
                    exc_info=True
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error sending review request for appointment {appointment.id}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {sent_count} review requests sent, {error_count} errors"
            )
        )
