"""
Email notification signals for contact app.

Sends emails when contact form is submitted.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone

from .models import ContactMessage

logger = logging.getLogger(__name__)

INTERNAL_EMAIL = "meister.barbershop.erlangen@gmail.com"


def send_email_with_template(
    subject: str,
    template_name: str,
    context: dict,
    to_emails: list[str],
    from_email: str | None = None,
):
    """Send an email using HTML and plain text templates."""
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

        logger.info(f"Email sent successfully: subject='{subject}', to={to_emails}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: subject='{subject}', to={to_emails}, error={str(e)}")
        return False


@receiver(post_save, sender=ContactMessage)
def send_contact_form_notification(sender, instance, created, **kwargs):
    """
    Send internal notification when contact form is submitted.
    Optionally send auto-reply to submitter if they provided an email.
    """
    if not created:
        return

    # Prepare context
    context = {
        "name": instance.name,
        "email": instance.email or "Not provided",
        "phone": instance.phone or "Not provided",
        "message": instance.message,
        "created_at": timezone.localtime(instance.created_at).strftime("%Y-%m-%d %H:%M"),
        "contact_id": instance.pk,
    }

    # Send internal notification
    send_email_with_template(
        subject=f"New Contact Form Message from {instance.name}",
        template_name="internal_contact",
        context=context,
        to_emails=[INTERNAL_EMAIL],
    )

    # Optional: Send auto-reply to submitter if they provided an email
    if instance.email:
        reply_context = {
            "name": instance.name,
        }
        send_email_with_template(
            subject="Thank you for contacting Meister Barbershop",
            template_name="contact_autoreply",
            context=reply_context,
            to_emails=[instance.email],
        )
