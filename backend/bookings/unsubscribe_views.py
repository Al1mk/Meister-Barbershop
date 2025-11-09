"""
Unsubscribe views for follow-up email opt-out functionality.
"""

import hmac
import hashlib
import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import FollowUpRequest

logger = logging.getLogger('meister.email')


def verify_unsubscribe_token(email: str, token: str) -> bool:
    """Verify HMAC token for unsubscribe link."""
    secret = settings.SECRET_KEY.encode('utf-8')
    message = email.lower().strip().encode('utf-8')
    expected_token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(token, expected_token)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def unsubscribe_followup(request):
    """
    Handle unsubscribe requests for follow-up emails.
    
    GET: Display confirmation page
    POST: Process unsubscribe and show success message
    """
    email = request.GET.get('email', '').lower().strip()
    token = request.GET.get('token', '')

    # Validate inputs
    if not email or not token:
        return render(request, 'emails/unsubscribe_error.html', {
            'error_de': 'Ungültiger Abmelde-Link.',
            'error_en': 'Invalid unsubscribe link.',
        }, status=400)

    # Verify token
    if not verify_unsubscribe_token(email, token):
        logger.warning(f"Invalid unsubscribe token for email: {email}")
        return render(request, 'emails/unsubscribe_error.html', {
            'error_de': 'Ungültiger oder abgelaufener Abmelde-Link.',
            'error_en': 'Invalid or expired unsubscribe link.',
        }, status=400)

    if request.method == 'POST':
        # Process unsubscribe
        try:
            followup, created = FollowUpRequest.objects.get_or_create(
                email=email,
                defaults={'opt_out': True, 'opted_out_at': timezone.now()}
            )
            
            if not created and not followup.opt_out:
                followup.opt_out = True
                followup.opted_out_at = timezone.now()
                followup.save(update_fields=['opt_out', 'opted_out_at'])
            
            logger.info(f"Email unsubscribed from follow-ups: {email}")
            
            return render(request, 'emails/unsubscribe_success.html', {
                'email': email,
            })
        
        except Exception as e:
            logger.error(f"Error processing unsubscribe for {email}: {e}", exc_info=True)
            return render(request, 'emails/unsubscribe_error.html', {
                'error_de': 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.',
                'error_en': 'An error occurred. Please try again later.',
            }, status=500)
    
    # GET request - show confirmation page
    return render(request, 'emails/unsubscribe_confirm.html', {
        'email': email,
        'token': token,
    })
