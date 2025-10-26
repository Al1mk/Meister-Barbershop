"""
Notification utilities for sending emails and SMS to customers.
"""
import logging
import re
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

# Shop details
SHOP_ADDRESS = "Hauptstr. 12, Erlangen"
GOOGLE_MAPS_LINK = "https://goo.gl/maps/nV1qv6F5m8Zb3j8Q6"
GOOGLE_REVIEW_LINK = "https://g.page/r/YOUR_PLACE_ID/review"  # Replace with actual Google review link


def normalize_phone_number(phone: str) -> str | None:
    """
    Normalize phone number to international format for Twilio.
    Returns None if phone is invalid.

    Examples:
        "0176 1234 5678" -> "+491761234567"
        "+49 176 1234567" -> "+491761234567"
        "176 1234567" -> "+491761234567"
    """
    if not phone:
        return None

    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    if not digits:
        return None

    # Handle German numbers
    if digits.startswith('49'):
        # Already has country code
        return f'+{digits}'
    elif digits.startswith('0'):
        # Remove leading 0 and add +49
        return f'+49{digits[1:]}'
    else:
        # Assume it's missing both +49 and leading 0
        return f'+49{digits}'


def send_email_notification(to_email: str, subject: str, message: str) -> bool:
    """
    Send email notification using Django's email backend.
    Returns True if successful, False otherwise.
    """
    try:
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_sms_notification(to_phone: str, message: str) -> bool:
    """
    Send SMS notification using Twilio.
    Returns True if successful, False otherwise.
    """
    # Check if Twilio is configured
    if not all([
        getattr(settings, 'TWILIO_ACCOUNT_SID', None),
        getattr(settings, 'TWILIO_AUTH_TOKEN', None),
        getattr(settings, 'TWILIO_FROM_NUMBER', None),
    ]):
        logger.warning("Twilio not configured, skipping SMS")
        return False

    # Normalize phone number
    normalized_phone = normalize_phone_number(to_phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {to_phone}, skipping SMS")
        return False

    try:
        from twilio.rest import Client

        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

        message_obj = client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=normalized_phone
        )

        logger.info(f"SMS sent successfully to {normalized_phone}, SID: {message_obj.sid}")
        return True
    except ImportError:
        logger.warning("Twilio library not installed, skipping SMS")
        return False
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
        return False


def format_appointment_datetime(dt) -> str:
    """
    Format appointment datetime for display.
    Example: "Tue 22 Oct, 14:30"
    """
    local_dt = timezone.localtime(dt)
    return local_dt.strftime("%a %d %b, %H:%M")


def send_confirmation_notification(appointment):
    """
    Send immediate confirmation email + SMS when appointment is created.
    """
    customer = appointment.customer
    barber = appointment.barber

    # Get customer first name
    first_name = customer.name.split()[0] if customer.name else "Customer"

    # Format appointment time
    appt_time = format_appointment_datetime(appointment.start_at)

    # Build email message
    email_subject = f"Appointment Confirmed - Meister Barbershop"
    email_message = f"""Hi {first_name},

Your appointment at Meister Barbershop has been confirmed!

Details:
- Barber: {barber.name}
- Time: {appt_time}
- Address: {SHOP_ADDRESS}
- Maps: {GOOGLE_MAPS_LINK}

Please arrive on time.

We look forward to seeing you!

Best regards,
Meister Barbershop Team
"""

    # Build SMS message
    sms_message = f"Hi {first_name}! Your haircut with {barber.name} is confirmed for {appt_time}. Address: {SHOP_ADDRESS}. {GOOGLE_MAPS_LINK}. Please be on time."

    # Send email
    email_sent = send_email_notification(customer.email, email_subject, email_message)

    # Send SMS (don't block if it fails)
    sms_sent = send_sms_notification(customer.phone, sms_message)

    # Update confirmation timestamp
    if email_sent or sms_sent:
        appointment.confirmation_sent_at = timezone.now()
        appointment.save(update_fields=['confirmation_sent_at'])

    return email_sent, sms_sent


def send_reminder_notification(appointment):
    """
    Send 2-hour reminder email + SMS before appointment.
    """
    customer = appointment.customer
    barber = appointment.barber

    first_name = customer.name.split()[0] if customer.name else "Customer"
    appt_time = format_appointment_datetime(appointment.start_at)

    # Build email message
    email_subject = "Reminder: Your Appointment Today"
    email_message = f"""Hi {first_name},

This is a friendly reminder about your appointment today:

- Barber: {barber.name}
- Time: {appt_time}
- Address: {SHOP_ADDRESS}
- Maps: {GOOGLE_MAPS_LINK}

Please be on time 🙌

See you soon!
Meister Barbershop Team
"""

    # Build SMS message
    sms_message = f"Reminder: your haircut at Meister Barbershop is today at {appt_time}. Address: {SHOP_ADDRESS}. Please be on time 🙌"

    # Send notifications
    email_sent = send_email_notification(customer.email, email_subject, email_message)
    sms_sent = send_sms_notification(customer.phone, sms_message)

    return email_sent, sms_sent


def send_review_request_notification(appointment):
    """
    Send review request email + SMS after appointment.
    """
    customer = appointment.customer

    first_name = customer.name.split()[0] if customer.name else "Customer"

    # Build email message
    email_subject = "Thanks for visiting Meister Barbershop 💈"
    email_message = f"""Hi {first_name},

We hope you enjoyed your cut today!

We'd love if you could leave us a quick rating on Google ⭐

Your feedback helps us a lot.

Leave a review here: {GOOGLE_REVIEW_LINK}

Thank you!
Meister Barbershop Team
"""

    # Build SMS message
    sms_message = f"Thanks for visiting Meister Barbershop! We'd love a quick Google review ⭐: {GOOGLE_REVIEW_LINK}. Your feedback helps us!"

    # Send notifications
    email_sent = send_email_notification(customer.email, email_subject, email_message)
    sms_sent = send_sms_notification(customer.phone, sms_message)

    return email_sent, sms_sent
