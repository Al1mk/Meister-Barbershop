"""
Unsubscribe views for follow-up email opt-out functionality with GDPR compliance.
Implements 48-hour token expiry and IP tracking.
"""

import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import FollowUpRequest
from .utils.email_helpers import verify_unsubscribe_token, generate_unsubscribe_token

logger = logging.getLogger('meister.email')


def get_client_ip(request) -> str:
    """Extract client IP address from request, handling proxy headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_exempt
@require_http_methods(["GET", "POST"])
def unsubscribe_followup(request):
    """
    Handle unsubscribe requests for follow-up emails with GDPR compliance.
    Implements 48-hour token expiry. If expired, allows email lookup with one-click confirm.

    GET: Display confirmation page
    POST: Process unsubscribe and show success message
    """
    email = request.GET.get('email', '').lower().strip()
    token = request.GET.get('token', '')

    # Validate inputs
    if not email or not token:
        return render(request, 'emails/unsubscribe_error.html', {
            'error_de': 'Ungültiger Abmelde-Link. Bitte überprüfen Sie den Link aus Ihrer E-Mail.',
            'error_en': 'Invalid unsubscribe link. Please check the link from your email.',
        }, status=400)

    # Verify token with 48h expiry
    token_valid = verify_unsubscribe_token(email, token, max_age_hours=48)

    if not token_valid:
        logger.warning(f"Invalid or expired unsubscribe token for email: {email}")

        # Token expired - offer email lookup with one-click confirm
        return render(request, 'emails/unsubscribe_expired.html', {
            'email': email,
            'new_token': generate_unsubscribe_token(email),  # Generate fresh token
            'error_de': 'Dieser Abmelde-Link ist abgelaufen (älter als 48 Stunden).',
            'error_en': 'This unsubscribe link has expired (older than 48 hours).',
        }, status=400)

    if request.method == 'POST':
        # Process unsubscribe with IP tracking
        try:
            client_ip = get_client_ip(request)

            # Find existing record or create opt-out entry
            existing = FollowUpRequest.objects.filter(email=email).first()

            if existing:
                if not existing.opt_out:
                    existing.opt_out = True
                    existing.opted_out_at = timezone.now()
                    existing.opted_out_ip = client_ip
                    existing.save(update_fields=['opt_out', 'opted_out_at', 'opted_out_ip'])
                    logger.info(f"Email opted out from follow-ups: {email} (IP: {client_ip})")
            else:
                # Create new opt-out record
                FollowUpRequest.objects.create(
                    email=email,
                    opt_out=True,
                    opted_out_at=timezone.now(),
                    opted_out_ip=client_ip
                )
                logger.info(f"New email opted out (no prior follow-up): {email} (IP: {client_ip})")

            return render(request, 'emails/unsubscribe_success.html', {
                'email': email,
            })

        except Exception as e:
            logger.error(f"Error processing unsubscribe for {email}: {e}", exc_info=True)
            return render(request, 'emails/unsubscribe_error.html', {
                'error_de': 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.',
                'error_en': 'An error occurred. Please try again later.',
            }, status=500)

    # GET request - show bilingual confirmation page (DE first, EN second)
    return render(request, 'emails/unsubscribe_confirm.html', {
        'email': email,
        'token': token,
    })
