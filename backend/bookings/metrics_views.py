"""
Email metrics endpoint for monitoring follow-up email system health.
"""
import logging
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import FollowUpRequest

logger = logging.getLogger('meister.email')


@require_http_methods(["GET"])
def email_metrics(request):
    """
    Expose email system metrics as JSON.

    Returns:
        - last_run_at: Timestamp of most recent follow-up sent
        - sent_count_24h: Number of follow-ups sent in last 24 hours
        - sent_count_7d: Number of follow-ups sent in last 7 days
        - opt_out_count: Total number of opted-out emails
        - bounce_count: Total number of bounced emails
        - complaint_count: Total number of spam complaints
        - cooldown_active_count: Emails currently in cooldown period
    """
    try:
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        # Get last run timestamp
        last_followup = FollowUpRequest.objects.filter(
            opt_out=False,
            appointment__isnull=False
        ).order_by('-sent_at').first()

        last_run_at = last_followup.sent_at.isoformat() if last_followup else None

        # Count metrics
        sent_count_24h = FollowUpRequest.objects.filter(
            sent_at__gte=last_24h,
            opt_out=False,
            appointment__isnull=False
        ).count()

        sent_count_7d = FollowUpRequest.objects.filter(
            sent_at__gte=last_7d,
            opt_out=False,
            appointment__isnull=False
        ).count()

        opt_out_count = FollowUpRequest.objects.filter(opt_out=True).count()

        bounce_count = FollowUpRequest.objects.filter(
            bounce_type__isnull=False
        ).count()

        complaint_count = FollowUpRequest.objects.filter(complaint=True).count()

        # Cooldown period
        from django.conf import settings
        cooldown_days = getattr(settings, 'FOLLOWUP_EMAIL_COOLDOWN_DAYS', 60)
        cooldown_cutoff = now - timedelta(days=cooldown_days)

        cooldown_active_count = FollowUpRequest.objects.filter(
            sent_at__gte=cooldown_cutoff,
            opt_out=False
        ).values('email').distinct().count()

        metrics = {
            'status': 'ok',
            'timestamp': now.isoformat(),
            'last_run_at': last_run_at,
            'sent_count_24h': sent_count_24h,
            'sent_count_7d': sent_count_7d,
            'opt_out_count': opt_out_count,
            'bounce_count': bounce_count,
            'complaint_count': complaint_count,
            'cooldown_active_count': cooldown_active_count,
            'cooldown_period_days': cooldown_days,
        }

        return JsonResponse(metrics)

    except Exception as e:
        logger.error(f"Error generating email metrics: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
