"""
Management command to send 2-hour follow-up emails requesting Google reviews.

This command should be run periodically (e.g., every 5 minutes via cron or systemd timer).
It finds appointments created at least 2 hours ago that haven't received a followup yet,
sends them a review request email, and marks them as sent.
"""

import logging
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from bookings.models import Appointment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send 2-hour follow-up emails requesting Google reviews"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails or updating database',
        )
        parser.add_argument(
            '--max-emails',
            type=int,
            default=50,
            help='Maximum number of emails to send in one run (default: 50)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_emails = options['max_emails']

        # Find appointments eligible for follow-up
        cutoff = timezone.now() - timedelta(hours=2)

        candidates = Appointment.objects.filter(
            followup_sent=False,
            created_at__lte=cutoff,
            status='booked',  # Only send to active appointments
        ).select_related('customer', 'barber').order_by('created_at')[:max_emails]

        count = candidates.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No appointments eligible for follow-up'))
            return

        self.stdout.write(self.style.WARNING(f'Found {count} appointment(s) eligible for follow-up'))

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN - No emails will be sent, no database changes'))

        # Get Google Place ID for review link
        place_id = settings.GOOGLE_PLACE_ID if hasattr(settings, 'GOOGLE_PLACE_ID') else None
        if place_id:
            review_link = f"https://search.google.com/local/writereview?placeid={place_id}"
        else:
            review_link = "https://maps.app.goo.gl/VuWm9gBnDSpViTHw9"
            self.stdout.write(self.style.WARNING('GOOGLE_PLACE_ID not configured, using fallback URL'))

        sent_count = 0
        failed_count = 0

        for appt in candidates:
            if not appt.customer or not appt.customer.email:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Appointment {appt.pk}: No customer email, skipping'
                    )
                )
                continue

            self.stdout.write(
                f'  Appointment {appt.pk}: {appt.customer.name} ({appt.customer.email}) '
                f'- created {timezone.localtime(appt.created_at).strftime("%Y-%m-%d %H:%M")}'
            )

            if dry_run:
                self.stdout.write(self.style.NOTICE('    [DRY RUN] Would send follow-up email'))
                sent_count += 1
                continue

            # Send follow-up email
            context = {
                "customer_name": appt.customer.name,
                "barber_name": appt.barber.name if appt.barber else "our team",
                "appointment_date": timezone.localtime(appt.start_at).strftime("%A, %B %d, %Y"),
                "appointment_time": timezone.localtime(appt.start_at).strftime("%H:%M"),
                "review_link": review_link,
                "place_id": place_id,
            }

            try:
                html_content = render_to_string("emails/followup.html", context)
                text_content = render_to_string("emails/followup.txt", context)

                msg = EmailMultiAlternatives(
                    subject="Share your experience at Meister Barbershop",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[appt.customer.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                # Mark as sent
                appt.followup_sent = True
                appt.followup_sent_at = timezone.now()
                appt.save(update_fields=['followup_sent', 'followup_sent_at'])

                self.stdout.write(self.style.SUCCESS('    ✓ Follow-up email sent'))
                sent_count += 1

                logger.info(
                    f"Follow-up email sent: appointment_id={appt.pk}, "
                    f"customer={appt.customer.email}, "
                    f"sent_at={timezone.now().isoformat()}"
                )

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'    ✗ Failed to send: {str(e)}'))
                logger.error(
                    f"Failed to send follow-up email: appointment_id={appt.pk}, "
                    f"customer={appt.customer.email if appt.customer else 'N/A'}, "
                    f"error={str(e)}"
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Summary: {sent_count} sent, {failed_count} failed'))

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN completed - no actual changes made'))
