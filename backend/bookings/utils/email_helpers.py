"""
Enhanced email helpers with List-Unsubscribe, UTM params, and provider integration.
"""
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
import requests

logger = logging.getLogger('meister.email')


def generate_unsubscribe_token(email: str, timestamp: int = None) -> str:
    """
    Generate HMAC token for unsubscribe link with 48h expiry.

    Args:
        email: Customer email address
        timestamp: Unix timestamp (defaults to now)

    Returns:
        Token string in format: {timestamp}:{hmac_hash}
    """
    if timestamp is None:
        timestamp = int(timezone.now().timestamp())

    secret = settings.SECRET_KEY.encode('utf-8')
    message = f"{email.lower().strip()}:{timestamp}".encode('utf-8')
    hmac_hash = hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]

    return f"{timestamp}:{hmac_hash}"


def verify_unsubscribe_token(email: str, token: str, max_age_hours: int = 48) -> bool:
    """
    Verify HMAC token for unsubscribe link with expiry check.

    Args:
        email: Customer email address
        token: Token string in format {timestamp}:{hmac_hash}
        max_age_hours: Maximum age in hours (default 48)

    Returns:
        True if valid and not expired, False otherwise
    """
    try:
        timestamp_str, hmac_hash = token.split(':', 1)
        timestamp = int(timestamp_str)

        # Check expiry
        now = int(timezone.now().timestamp())
        max_age_seconds = max_age_hours * 3600
        if now - timestamp > max_age_seconds:
            logger.warning(f"Unsubscribe token expired for {email}")
            return False

        # Verify HMAC
        expected_token = generate_unsubscribe_token(email, timestamp)
        expected_hash = expected_token.split(':', 1)[1]

        return hmac.compare_digest(hmac_hash, expected_hash)

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid unsubscribe token format: {e}")
        return False


def add_utm_params(url: str, source: str = 'email', medium: str = 'followup', campaign: str = 'review_request') -> str:
    """Add UTM parameters to URL for analytics tracking."""
    separator = '&' if '?' in url else '?'
    return f"{url}{separator}utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"


def send_email_with_template(
    subject: str,
    template_name: str,
    context: dict,
    to_emails: list,
    from_email: str = None,
    attachments: list = None,
    headers: dict = None
) -> tuple:
    """
    Send email using Django templates with both HTML and plain text versions.
    Adds List-Unsubscribe header for follow-up emails.

    Args:
        subject: Email subject
        template_name: Template name (without .html/.txt extension)
        context: Template context dictionary
        to_emails: List of recipient email addresses
        from_email: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
        attachments: List of tuples (filename, content, mimetype)
        headers: Additional email headers

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        # Enhance context with site URLs and UTM params
        enhanced_context = {
            **context,
            'site_url': settings.SITE_URL,
            'imprint_url': getattr(settings, 'SITE_IMPRINT_URL', f"{settings.SITE_URL}/impressum"),
            'privacy_url': getattr(settings, 'SITE_PRIVACY_URL', f"{settings.SITE_URL}/datenschutz"),
        }

        # Add Google Review link with UTM params if in context
        if 'review_link' in context:
            enhanced_context['review_link'] = add_utm_params(
                context['review_link'],
                source='email',
                medium='followup',
                campaign='review_request'
            )

        # Render templates
        html_content = render_to_string(f'emails/{template_name}.html', enhanced_context)
        text_content = render_to_string(f'emails/{template_name}.txt', enhanced_context)

        # Create email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails
        )
        msg.attach_alternative(html_content, "text/html")

        # Add List-Unsubscribe headers for follow-up emails
        if headers is None:
            headers = {}

        if 'unsubscribe_link' in context:
            unsubscribe_url = context['unsubscribe_link']
            # RFC 8058 compliant List-Unsubscribe and List-Unsubscribe-Post
            headers['List-Unsubscribe'] = f'<{unsubscribe_url}>'
            headers['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

        # Add custom headers
        for key, value in headers.items():
            msg.extra_headers[key] = value

        # Add attachments
        if attachments:
            for filename, content, mimetype in attachments:
                msg.attach(filename, content, mimetype)

        # Send email
        msg.send(fail_silently=False)

        logger.info(f"Email sent successfully: {template_name} to {', '.join(to_emails)}")
        return (True, None)

    except Exception as e:
        error_msg = f"Failed to send email {template_name} to {', '.join(to_emails)}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return (False, error_msg)


def send_telegram_alert(message: str) -> bool:
    """
    Send alert to Telegram group.

    Args:
        message: Alert message text

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)

        if not bot_token or not chat_id:
            logger.warning("Telegram credentials not configured, skipping alert")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        logger.info("Telegram alert sent successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
