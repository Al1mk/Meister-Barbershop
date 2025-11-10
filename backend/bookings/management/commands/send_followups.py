"""
Management command to send 2-hour follow-up emails requesting Google reviews.

HARDENED VERSION with:
- ONE follow-up per appointment (not per email)
- 60-day cooldown per email (configurable via FOLLOWUP_EMAIL_COOLDOWN_DAYS)
- Status filter: only completed/attended appointments
- Timezone-aware scheduling (Europe/Berlin)
- List-Unsubscribe headers
- Telegram alerts on high failure rates
- Detailed per-appointment skip reasons in dry-run mode
- Comprehensive metrics tracking

This command should be run periodically (e.g., every 5 minutes via systemd timer).
"""

import logging
import pytz
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from bookings.email_helpers import build_review_url, unsubscribe_followup_url

from bookings.models import Appointment, FollowUpRequest
from bookings.utils.email_helpers import (
    generate_unsubscribe_token,
    send_email_with_template,
    send_telegram_alert,
    add_utm_params,
)

logger = logging.getLogger('meister.email')


class Command(BaseCommand):
    help = "Send 2-hour follow-up emails requesting Google reviews (hardened, per-appointment with cooldown)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent with detailed skip reasons, no emails or database changes',
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

        # Use Europe/Berlin timezone for all scheduling
        berlin_tz = pytz.timezone('Europe/Berlin')
        now = timezone.now().astimezone(berlin_tz)
        cutoff = now - timedelta(hours=2)

        # Get cooldown period (default 60 days)
        cooldown_days = getattr(settings, 'FOLLOWUP_EMAIL_COOLDOWN_DAYS', 60)
        cooldown_cutoff = now - timedelta(days=cooldown_days)

        # Get appointments that already have follow-ups (one-to-one relationship)
        appointments_with_followups = set(
            FollowUpRequest.objects.filter(appointment__isnull=False)
            .values_list('appointment_id', flat=True)
        )

        # Get emails that opted out
        opted_out_emails = set(
            FollowUpRequest.objects.filter(opt_out=True).values_list('email', flat=True)
        )

        # Get emails that received follow-ups within cooldown period
        recent_followup_emails = set(
            FollowUpRequest.objects.filter(
                sent_at__gte=cooldown_cutoff,
                opt_out=False
            ).values_list('email', flat=True)
        )

        # Find eligible appointments:
        # - Status must be 'completed' or 'attended' (NOT booked, cancelled, no-show)
        # - Appointment start time at least 2 hours ago
        # - Not already sent follow-up
        # - Has customer email
        # - Customer email not opted out
        # - Customer email not in cooldown period
        # - Appointment doesn't have a FollowUpRequest yet
        candidates = Appointment.objects.filter(
            status__in=['completed', 'attended'],  # Only completed/attended
            start_at__lte=cutoff,  # At least 2h after appointment start (not creation)
            customer__email__isnull=False,
        ).exclude(
            id__in=appointments_with_followups  # No follow-up sent for this appointment
        ).exclude(
            customer__email__in=opted_out_emails  # Not opted out
        ).exclude(
            customer__email__in=recent_followup_emails  # Not in cooldown period
        ).select_related('customer', 'barber').order_by('start_at')[:max_emails * 2]  # Get more for filtering

        # Manual filtering for detailed skip reasons in dry-run
        eligible = []
        skip_reasons = {}

        for appt in candidates:
            customer_email = appt.customer.email.lower().strip() if appt.customer else None

            if not customer_email:
                skip_reasons[appt.pk] = "No customer email"
                continue

            if customer_email in opted_out_emails:
                skip_reasons[appt.pk] = "Customer opted out"
                continue

            if customer_email in recent_followup_emails:
                last_followup = FollowUpRequest.objects.filter(
                    email=customer_email,
                    sent_at__gte=cooldown_cutoff
                ).order_by('-sent_at').first()
                days_ago = (now - last_followup.sent_at).days if last_followup else 0
                skip_reasons[appt.pk] = f"Cooldown active (last follow-up {days_ago} days ago, need {cooldown_days})"
                continue

            if appt.pk in appointments_with_followups:
                skip_reasons[appt.pk] = "Follow-up already sent for this appointment"
                continue

            if appt.status not in ['completed', 'attended']:
                skip_reasons[appt.pk] = f"Status is '{appt.status}' (need completed/attended)"
                continue

            if appt.start_at > cutoff:
                skip_reasons[appt.pk] = "Appointment start time < 2 hours ago"
                continue

            eligible.append(appt)

            if len(eligible) >= max_emails:
                break

        count = len(eligible)
        skipped_count = len(skip_reasons)

        if count == 0 and skipped_count == 0:
            self.stdout.write(self.style.SUCCESS('No appointments eligible for follow-up'))
            return

        self.stdout.write(self.style.WARNING(
            f'Found {count} appointment(s) eligible for follow-up, {skipped_count} skipped'
        ))

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN - No emails will be sent, no database changes'))
            self.stdout.write('')

        # Show skip reasons in dry-run
        if dry_run and skip_reasons:
            self.stdout.write(self.style.NOTICE('Skipped appointments:'))
            for appt_id, reason in list(skip_reasons.items())[:20]:  # Show first 20
                self.stdout.write(f'  Appointment {appt_id}: {reason}')
            if len(skip_reasons) > 20:
                self.stdout.write(f'  ... and {len(skip_reasons) - 20} more')
            self.stdout.write('')

        if count == 0:
            return

        # Get Google Place ID for review link
        place_id = getattr(settings, 'GOOGLE_PLACE_ID', 'ChIJRWUULEz5oUcRhfnp-cp0dXs')
        review_link = f"https://search.google.com/local/writereview?placeid={place_id}"

        sent_count = 0
        failed_count = 0

        for appt in eligible:
            customer_email = appt.customer.email.lower().strip()

            self.stdout.write(
                f'  Appointment {appt.pk}: {appt.customer.name} ({customer_email}) '
                f'- started {timezone.localtime(appt.start_at).strftime("%Y-%m-%d %H:%M")} '
                f'- status: {appt.status}'
            )

            if dry_run:
                self.stdout.write(self.style.NOTICE('    [DRY RUN] Would send follow-up email'))
                sent_count += 1
                continue

            # Generate unsubscribe link with timestamp
            token = generate_unsubscribe_token(customer_email)
            base_url = getattr(settings, 'SITE_URL', 'https://www.meisterbarbershop.de')
            unsubscribe_params = urlencode({'email': customer_email, 'token': token})
            unsubscribe_link = f"{base_url}/unsubscribe-followup/?{unsubscribe_params}"

            # Add UTM parameters to review link
            review_link_with_utm = add_utm_params(
                review_link,
                source='email',
                medium='followup',
                campaign='review_request'
            )

            # Prepare email context
            context = {
                "customer_name": appt.customer.name,
                "barber_name": appt.barber.name if appt.barber else "unser Team / our team",
                "appointment_date": timezone.localtime(appt.start_at).strftime("%A, %d. %B %Y"),
                "appointment_time": timezone.localtime(appt.start_at).strftime("%H:%M"),
                "service_type": appt.get_service_type_display(),
                "review_link": review_link_with_utm,
                "unsubscribe_link": unsubscribe_link,
            }

            try:
                # Send email using enhanced helper
                success, error = send_email_with_template(
                    subject="Ihre Meinung zählt! / Your feedback matters - Meister Barbershop",
                    template_name="appointment_followup_review",
                    context=context,
                    to_emails=[customer_email],
                )

                if not success:
                    raise Exception(error)

                # Create FollowUpRequest record (one-to-one with appointment)
                FollowUpRequest.objects.create(
                    email=customer_email,
                    phone=appt.customer.phone if appt.customer else None,
                    appointment=appt,  # ONE-TO-ONE relationship
                    lang='de',  # Default to German
                )

                self.stdout.write(self.style.SUCCESS('    ✓ Follow-up email sent'))
                sent_count += 1

                logger.info(
                    f"Follow-up email sent: appointment_id={appt.pk}, "
                    f"customer={customer_email}, "
                    f"status={appt.status}, "
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

        # Calculate failure rate
        total_attempted = sent_count + failed_count
        failure_rate = (failed_count / total_attempted * 100) if total_attempted > 0 else 0

        # Summary
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: {sent_count} sent, {failed_count} failed ({failure_rate:.1f}% failure rate)'
            )
        )

        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN completed - no actual changes made'))
        else:
            # Send Telegram alert if failure rate > 5%
            if failure_rate > 5.0 and total_attempted > 0:
                alert_message = (
                    f"⚠️ *Email System Alert*\n\n"
                    f"High failure rate detected in follow-up emails:\n"
                    f"• Sent: {sent_count}\n"
                    f"• Failed: {failed_count}\n"
                    f"• Failure rate: {failure_rate:.1f}%\n\n"
                    f"Please check `/var/log/meister-email.log` for details."
                )
                send_telegram_alert(alert_message)
                logger.warning(f"High failure rate alert sent: {failure_rate:.1f}%")

        logger.info(
            f"Follow-up batch completed: sent={sent_count}, failed={failed_count}, "
            f"skipped={skipped_count}, failure_rate={failure_rate:.1f}%"
        )
