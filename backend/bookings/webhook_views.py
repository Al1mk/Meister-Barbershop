"""
Webhook handlers for email provider events (bounces, complaints, unsubscribes).
Supports Mailgun and Sendgrid webhooks.
"""
import logging
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import FollowUpRequest

logger = logging.getLogger('meister.email')


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_exempt
@require_http_methods(["POST"])
def mailgun_webhook(request):
    """
    Handle Mailgun webhook events for bounces and complaints.

    Event types:
    - failed: permanent (hard bounce) or temporary (soft bounce)
    - complained: spam complaint
    """
    try:
        # Parse webhook data
        event_data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()

        event_type = event_data.get('event')
        recipient = event_data.get('recipient', '').lower().strip()

        if not recipient:
            logger.warning("Mailgun webhook missing recipient")
            return JsonResponse({'status': 'ignored', 'reason': 'no recipient'}, status=200)

        logger.info(f"Mailgun webhook received: event={event_type}, recipient={recipient}")

        # Handle bounce events
        if event_type == 'failed':
            severity = event_data.get('severity', 'temporary')
            reason = event_data.get('reason', 'Unknown')
            error = event_data.get('delivery-status', {}).get('message', '')

            # Create or update FollowUpRequest
            followup, created = FollowUpRequest.objects.get_or_create(
                email=recipient,
                defaults={
                    'opt_out': True if severity == 'permanent' else False,
                    'opted_out_at': timezone.now() if severity == 'permanent' else None,
                    'bounce_type': severity,
                    'webhook_event_data': event_data,
                }
            )

            if not created:
                if severity == 'permanent':
                    followup.opt_out = True
                    followup.opted_out_at = timezone.now()
                followup.bounce_type = severity
                followup.webhook_event_data = event_data
                followup.save(update_fields=['opt_out', 'opted_out_at', 'bounce_type', 'webhook_event_data'])

            logger.warning(
                f"Email bounced: {recipient}, severity={severity}, reason={reason}, error={error}"
            )

        # Handle spam complaints
        elif event_type == 'complained':
            # Auto opt-out on spam complaint
            followup, created = FollowUpRequest.objects.get_or_create(
                email=recipient,
                defaults={
                    'opt_out': True,
                    'opted_out_at': timezone.now(),
                    'complaint': True,
                    'webhook_event_data': event_data,
                }
            )

            if not created:
                followup.opt_out = True
                followup.opted_out_at = timezone.now()
                followup.complaint = True
                followup.webhook_event_data = event_data
                followup.save(update_fields=['opt_out', 'opted_out_at', 'complaint', 'webhook_event_data'])

            logger.warning(f"Spam complaint received: {recipient}")

        return JsonResponse({'status': 'processed'}, status=200)

    except Exception as e:
        logger.error(f"Error processing Mailgun webhook: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def sendgrid_webhook(request):
    """
    Handle Sendgrid webhook events for bounces and complaints.

    Event types:
    - bounce: email bounced
    - dropped: email dropped due to bounce/spam
    - spamreport: spam complaint
    """
    try:
        # Sendgrid sends an array of events
        events = json.loads(request.body)

        if not isinstance(events, list):
            events = [events]

        for event_data in events:
            event_type = event_data.get('event')
            recipient = event_data.get('email', '').lower().strip()

            if not recipient:
                continue

            logger.info(f"Sendgrid webhook received: event={event_type}, recipient={recipient}")

            # Handle bounces
            if event_type in ['bounce', 'dropped', 'blocked']:
                bounce_type = event_data.get('type', 'unknown')  # hard, soft, or block
                reason = event_data.get('reason', 'Unknown')

                # Create or update FollowUpRequest
                followup, created = FollowUpRequest.objects.get_or_create(
                    email=recipient,
                    defaults={
                        'opt_out': True if bounce_type == 'hard' or event_type == 'dropped' else False,
                        'opted_out_at': timezone.now() if bounce_type == 'hard' or event_type == 'dropped' else None,
                        'bounce_type': bounce_type,
                        'webhook_event_data': event_data,
                    }
                )

                if not created:
                    if bounce_type == 'hard' or event_type == 'dropped':
                        followup.opt_out = True
                        followup.opted_out_at = timezone.now()
                    followup.bounce_type = bounce_type
                    followup.webhook_event_data = event_data
                    followup.save(update_fields=['opt_out', 'opted_out_at', 'bounce_type', 'webhook_event_data'])

                logger.warning(
                    f"Email bounced (Sendgrid): {recipient}, type={bounce_type}, reason={reason}"
                )

            # Handle spam reports
            elif event_type == 'spamreport':
                # Auto opt-out on spam complaint
                followup, created = FollowUpRequest.objects.get_or_create(
                    email=recipient,
                    defaults={
                        'opt_out': True,
                        'opted_out_at': timezone.now(),
                        'complaint': True,
                        'webhook_event_data': event_data,
                    }
                )

                if not created:
                    followup.opt_out = True
                    followup.opted_out_at = timezone.now()
                    followup.complaint = True
                    followup.webhook_event_data = event_data
                    followup.save(update_fields=['opt_out', 'opted_out_at', 'complaint', 'webhook_event_data'])

                logger.warning(f"Spam complaint received (Sendgrid): {recipient}")

            # Handle unsubscribe events
            elif event_type == 'unsubscribe':
                followup, created = FollowUpRequest.objects.get_or_create(
                    email=recipient,
                    defaults={
                        'opt_out': True,
                        'opted_out_at': timezone.now(),
                        'webhook_event_data': event_data,
                    }
                )

                if not created:
                    followup.opt_out = True
                    followup.opted_out_at = timezone.now()
                    followup.webhook_event_data = event_data
                    followup.save(update_fields=['opt_out', 'opted_out_at', 'webhook_event_data'])

                logger.info(f"Unsubscribe via Sendgrid: {recipient}")

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Error processing Sendgrid webhook: {e}", exc_info=True)
        return HttpResponse(status=500)
