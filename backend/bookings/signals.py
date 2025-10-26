"""
Django signals for appointment notifications.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from .notifications import send_confirmation_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def send_appointment_confirmation(sender, instance, created, **kwargs):
    """
    Send immediate confirmation email + SMS when appointment is created.
    Only runs on create, not on updates.
    """
    if not created:
        # This is an update, not a new appointment
        return

    if instance.status == 'cancelled':
        # Don't send confirmation for cancelled appointments
        return

    if instance.confirmation_sent_at:
        # Already sent confirmation
        return

    try:
        logger.info(f"Sending confirmation for appointment {instance.id}")
        email_sent, sms_sent = send_confirmation_notification(instance)

        if email_sent:
            logger.info(f"Confirmation email sent for appointment {instance.id}")
        if sms_sent:
            logger.info(f"Confirmation SMS sent for appointment {instance.id}")

    except Exception as e:
        logger.error(f"Error sending confirmation for appointment {instance.id}: {str(e)}")
        # Don't raise exception - we don't want to block the booking flow
