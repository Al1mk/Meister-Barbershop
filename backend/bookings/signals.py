import os
import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Appointment

logger = logging.getLogger(__name__)

NOTIFY_URL = os.getenv("TELEGRAM_NOTIFY_URL", "http://telegram-bot:8787/notify")
BOT_SECRET = os.getenv("TELEGRAM_BOT_SECRET", "")
INTERNAL_EMAIL = "meister.barbershop.erlangen@gmail.com"


def _post(payload: dict):
    """Send notification to Telegram bot"""
    if not BOT_SECRET:
        logger.error("TELEGRAM_BOT_SECRET missing - cannot send notification")
        return
    
    payload["secret"] = BOT_SECRET
    
    try:
        r = requests.post(NOTIFY_URL, json=payload, timeout=5)
        r.raise_for_status()
        logger.info(f"Telegram notification sent: {payload.get('event', 'unknown')}")
    except Exception as e:
        logger.exception(f"Telegram notify failed: {e}")


def _serialize(appt: Appointment) -> dict:
    """Serialize appointment for Telegram notification"""
    try:
        barber_name = getattr(appt.barber, "name", "") if appt.barber else ""
        customer_name = getattr(appt.customer, "name", "") if appt.customer else ""
        
        # Get service display name
        service_name = appt.get_service_type_display() if appt.service_type else ""
        if not service_name and appt.service_type:
            service_name = appt.service_type
        
        # Format time
        time_str = appt.start_at.strftime("%Y-%m-%d %H:%M") if appt.start_at else ""
        
        return {
            "id": appt.id,
            "customer": customer_name,
            "barber": barber_name,
            "service": service_name,
            "time": time_str,
            "status": appt.status,
            "notes": "",
        }
    except Exception as e:
        logger.exception(f"Error serializing appointment {appt.id}: {e}")
        return {
            "id": getattr(appt, "id", "unknown"),
            "customer": "Error",
            "barber": "Error",
            "service": "Error",
            "time": "Error",
            "status": "Error",
            "notes": str(e),
        }


def send_email_with_template(
    subject: str,
    template_name: str,
    context: dict,
    to_emails: list[str],
    from_email: str | None = None,
):
    """
    Send an email using HTML and plain text templates.

    Args:
        subject: Email subject line
        template_name: Base template name (without .html/.txt extension)
        context: Template context dictionary
        to_emails: List of recipient email addresses
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    """
    try:
        html_content = render_to_string(f"emails/{template_name}.html", context)
        text_content = render_to_string(f"emails/{template_name}.txt", context)

        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        logger.info(
            f"Email sent successfully: subject='{subject}', to={to_emails}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send email: subject='{subject}', to={to_emails}, error={str(e)}"
        )
        return False


@receiver(post_save, sender=Appointment)
def on_appointment_saved(sender, instance, created, **kwargs):
    """Handle appointment creation and updates"""
    event = "created" if created else "updated"

    payload = {
        "event": event,
        "appointment": _serialize(instance)
    }

    _post(payload)

    # Send email notifications on creation
    if created and instance.customer and instance.customer.email:
        # Prepare context for templates
        context = {
            "customer_name": instance.customer.name,
            "barber_name": instance.barber.name if instance.barber else "our team",
            "appointment_date": timezone.localtime(instance.start_at).strftime("%A, %B %d, %Y"),
            "appointment_time": timezone.localtime(instance.start_at).strftime("%H:%M"),
            "service_type": instance.get_service_type_display() if instance.service_type else "Haircut",
            "duration": instance.duration_minutes,
            "appointment_id": instance.pk,
        }

        # Send confirmation to customer
        customer_sent = send_email_with_template(
            subject=f"Appointment Confirmation - Meister Barbershop",
            template_name="confirmation",
            context=context,
            to_emails=[instance.customer.email],
        )

        if customer_sent:
            Appointment.objects.filter(pk=instance.pk).update(
                confirmation_sent_at=timezone.now()
            )

        # Send internal notification
        internal_context = {
            **context,
            "customer_phone": instance.customer.phone,
            "customer_email": instance.customer.email,
        }

        send_email_with_template(
            subject=f"New Appointment: {instance.customer.name} with {instance.barber.name}",
            template_name="internal_appointment",
            context=internal_context,
            to_emails=[INTERNAL_EMAIL],
        )


@receiver(post_delete, sender=Appointment)
def on_appointment_deleted(sender, instance, **kwargs):
    """Handle appointment deletion"""
    payload = {
        "event": "deleted",
        "appointment": _serialize(instance)
    }
    
    _post(payload)
