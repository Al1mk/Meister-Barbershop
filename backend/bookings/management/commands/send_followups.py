"""
Management command to send 2-hour follow-up emails requesting Google reviews.

Features:
- Bilingual emails (German + English)
- Single follow-up per email address (tracked via FollowUpRequest model)
- Respects opt-out preferences
- Includes unsubscribe link in every email
- Rate-limited (default 50 emails per run)
- Dry-run support for testing
- Comprehensive logging

This command should be run periodically (e.g., every 5 minutes via systemd timer).
"""

import logging
import hmac
import hashlib
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from bookings.models import Appointment, FollowUpRequest

logger = logging.getLogger('meister.email')


def generate_unsubscribe_token(email: str) -> str:
    """Generate HMAC token for unsubscribe link."""
    secret = settings.SECRET_KEY.encode('utf-8')
    message = email.lower().strip().encode('utf-8')
    return hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]


class Command(BaseCommand):
    help = "Send 2-hour follow-up emails requesting Google reviews (bilingual, single per customer)"

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

        # Get emails that already received follow-ups or opted out
        existing_followups = set(
            FollowUpRequest.objects.values_list('email', flat=True)
        )
        opted_out_emails = set(
            FollowUpRequest.objects.filter(opt_out=True).values_list('email', flat=True)
        )

        candidates = Appointment.objects.filter(
            followup_sent=False,
            created_at__lte=cutoff,
            status='booked',
            customer__email__isnull=False,
        ).exclude(
            customer__email__in=existing_followups
        ).select_related('customer', 'barber').order_by('created_at')[:max_emails]

        count = candidates.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No appointments eligible for follow-up'))
            return

        self.stdout.write(self.style.WARNING(f'Found {count} appointment(s) eligible for follow-up'))

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN - No emails will be sent, no database changes'))

        # Get Google Place ID for review link
        place_id = getattr(settings, 'GOOGLE_PLACE_ID', 'ChIJRWUULEz5oUcRhfnp-cp0dXs')
        review_link = f"https://search.google.com/local/writereview?placeid={place_id}"

        sent_count = 0
        failed_count = 0
        skipped_count = 0

        for appt in candidates:
            customer_email = appt.customer.email.lower().strip()

            # Double-check opt-out status
            if customer_email in opted_out_emails:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Appointment {appt.pk}: {customer_email} opted out, skipping'
                    )
                )
                skipped_count += 1
                continue

            if not customer_email:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Appointment {appt.pk}: No customer email, skipping'
                    )
                )
                skipped_count += 1
                continue

            self.stdout.write(
                f'  Appointment {appt.pk}: {appt.customer.name} ({customer_email}) '
                f'- created {timezone.localtime(appt.created_at).strftime("%Y-%m-%d %H:%M")}'
            )

            if dry_run:
                self.stdout.write(self.style.NOTICE('    [DRY RUN] Would send follow-up email'))
                sent_count += 1
                continue

            # Generate unsubscribe link
            token = generate_unsubscribe_token(customer_email)
            base_url = getattr(settings, 'SITE_URL', 'https://www.meisterbarbershop.de')
            unsubscribe_params = urlencode({'email': customer_email, 'token': token})
            unsubscribe_link = f"{base_url}/unsubscribe-followup/?{unsubscribe_params}"

            # Prepare email context
            context = {
                "customer_name": appt.customer.name,
                "barber_name": appt.barber.name if appt.barber else "unser Team / our team",
                "appointment_date": timezone.localtime(appt.start_at).strftime("%A, %d. %B %Y"),
                "appointment_time": timezone.localtime(appt.start_at).strftime("%H:%M"),
                "review_link": review_link,
                "unsubscribe_link": unsubscribe_link,
            }

            try:
                # Render bilingual templates
                html_content = render_to_string("emails/appointment_followup_review.html", context)
                text_content = render_to_string("emails/appointment_followup_review.txt", context)

                msg = EmailMultiAlternatives(
                    subject="Ihre Meinung zählt! / Your feedback matters - Meister Barbershop",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[customer_email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                # Create FollowUpRequest record
                FollowUpRequest.objects.create(
                    email=customer_email,
                    phone=appt.customer.phone if appt.customer else None,
                    appointment=appt,
                    lang='de',  # Default to German
                )

                # Mark appointment as followup sent
                Appointment.objects.filter(pk=appt.pk).update(
                    followup_sent=True,
                    followup_sent_at=timezone.now()
                )

                self.stdout.write(self.style.SUCCESS('    ✓ Follow-up email sent'))
                sent_count += 1

                logger.info(
                    f"Follow-up email sent: appointment_id={appt.pk}, "
                    f"customer={customer_email}, "
                    f"sent_at={timezone.now().isoformat()}"
                )

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                self.stdout.write(self.style.ERROR(f'    ✗ Failed to send: {error_msg}'))
                logger.error(
                    f"Failed to send follow-up email: appointment_id={appt.pk}, "
                    f"customer={customer_email}, "
                    f"error={error_msg}",
                    exc_info=True
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: {sent_count} sent, {failed_count} failed, {skipped_count} skipped'
            )
        )

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN completed - no actual changes made'))
