import os
import logging
import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Appointment

logger = logging.getLogger(__name__)

NOTIFY_URL = os.getenv("TELEGRAM_NOTIFY_URL", "http://telegram-bot:8787/notify")
BOT_SECRET = os.getenv("TELEGRAM_BOT_SECRET", "")


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


@receiver(post_save, sender=Appointment)
def on_appointment_saved(sender, instance, created, **kwargs):
    """Handle appointment creation and updates"""
    event = "created" if created else "updated"
    
    payload = {
        "event": event,
        "appointment": _serialize(instance)
    }
    
    _post(payload)


@receiver(post_delete, sender=Appointment)
def on_appointment_deleted(sender, instance, **kwargs):
    """Handle appointment deletion"""
    payload = {
        "event": "deleted",
        "appointment": _serialize(instance)
    }
    
    _post(payload)
