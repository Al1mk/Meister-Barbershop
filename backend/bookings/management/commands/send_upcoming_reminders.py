"""
Django management command to send 2-hour reminders for upcoming appointments.

Usage:
    python manage.py send_upcoming_reminders

This should be run via cron every 10 minutes.
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Appointment
from bookings.notifications import send_reminder_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminders for appointments starting in approximately 2 hours'

    def handle(self, *args, **options):
        now = timezone.now()

        # Find appointments starting in 90-150 minutes window
        # This prevents double-sending if cron drifts slightly
        start_window = now + timedelta(minutes=90)
        end_window = now + timedelta(minutes=150)

        self.stdout.write(
            f"Looking for appointments between {start_window} and {end_window}"
        )

        # Find eligible appointments
        appointments = Appointment.objects.filter(
            start_at__gte=start_window,
            start_at__lte=end_window,
            status='booked',  # Not cancelled or completed
            reminder_sent=False,  # Haven't sent reminder yet
        ).select_related('customer', 'barber')

        count = appointments.count()
        self.stdout.write(f"Found {count} appointment(s) needing reminders")

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No reminders to send"))
            return

        sent_count = 0
        error_count = 0

        for appointment in appointments:
            try:
                self.stdout.write(
                    f"Sending reminder for appointment {appointment.id} "
                    f"(Customer: {appointment.customer.name}, "
                    f"Barber: {appointment.barber.name}, "
                    f"Time: {appointment.start_at})"
                )

                email_sent, sms_sent = send_reminder_notification(appointment)

                if email_sent or sms_sent:
                    # Mark as sent
                    appointment.reminder_sent = True
                    appointment.save(update_fields=['reminder_sent'])
                    sent_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Reminder sent for appointment {appointment.id} "
                            f"(Email: {email_sent}, SMS: {sms_sent})"
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠ Failed to send reminder for appointment {appointment.id}"
                        )
                    )

            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error processing reminder for appointment {appointment.id}: {str(e)}",
                    exc_info=True
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error sending reminder for appointment {appointment.id}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {sent_count} reminders sent, {error_count} errors"
            )
        )
