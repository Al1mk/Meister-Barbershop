# Email Notification System

This document describes the email notification system for Meister Barbershop, including immediate confirmations and 2-hour follow-up review requests.

## Overview

The email system sends three types of emails:

1. **Appointment Confirmation** - Sent immediately when a customer books an appointment
2. **Internal Notification** - Sent to `meister.barbershop.erlangen@gmail.com` for new appointments and contact form submissions
3. **Follow-up Review Request** - Sent 2 hours after appointment creation, asking customers to leave a Google review

## Configuration

### Email Settings

Email configuration is stored in `/srv/meister/backend/.env`:

```bash
# Email Configuration (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=meister.barbershop.erlangen@gmail.com
GMAIL_APP_PASSWORD=__PLACEHOLDER__
DEFAULT_FROM_EMAIL=meister.barbershop.erlangen@gmail.com

# Google Reviews Configuration
GOOGLE_PLACE_ID=ChIJRWUULEz5oUcRhfnp-cp0dXs
```

### Updating the Gmail App Password

If you need to change the Gmail App Password:

1. Generate a new App Password from Google:
   - Go to https://myaccount.google.com/apppasswords
   - Sign in with `meister.barbershop.erlangen@gmail.com`
   - Generate a new App Password for "Mail"

2. Update the `.env` file on the server:
   ```bash
   ssh root@91.107.255.58
   cd /srv/meister/backend
   nano .env
   # Update GMAIL_APP_PASSWORD=your_new_password_here
   ```

3. Restart the backend service:
   ```bash
   cd /srv/meister
   docker compose restart backend
   ```

## Follow-up Email Job

### Systemd Timer (Recommended)

The follow-up emails are sent automatically every 5 minutes via systemd timer.

**Check timer status:**
```bash
systemctl status meister-send-followups.timer
systemctl status meister-send-followups.service
```

**View logs:**
```bash
journalctl -u meister-send-followups.service -f
```

**Manually trigger a run:**
```bash
systemctl start meister-send-followups.service
```

**Stop the timer:**
```bash
systemctl stop meister-send-followups.timer
systemctl disable meister-send-followups.timer
```

### Manual Execution

You can also run the follow-up job manually:

**Dry run (no emails sent, no database changes):**
```bash
cd /srv/meister/backend
docker compose exec backend python manage.py send_followups --dry-run
```

**Send follow-ups:**
```bash
cd /srv/meister/backend
docker compose exec backend python manage.py send_followups
```

**Limit the number of emails sent:**
```bash
docker compose exec backend python manage.py send_followups --max-emails=10
```

## Email Templates

Email templates are located in `/srv/meister/backend/templates/emails/`:

- `confirmation.html` / `confirmation.txt` - Appointment confirmation
- `followup.html` / `followup.txt` - 2-hour follow-up review request
- `internal_appointment.html` / `internal_appointment.txt` - Internal appointment notification
- `internal_contact.html` / `internal_contact.txt` - Internal contact form notification
- `contact_autoreply.html` / `contact_autoreply.txt` - Contact form auto-reply

### Customizing Templates

1. Edit the template files directly on the server
2. No restart required - templates are loaded dynamically
3. Test with a dry run first

## Troubleshooting

### Emails Not Sending

1. **Check Gmail App Password:**
   ```bash
   # Verify password is set (don't print it!)
   grep GMAIL_APP_PASSWORD /srv/meister/backend/.env
   ```

2. **Check logs:**
   ```bash
   # Backend container logs
   docker compose logs backend --tail=100 -f

   # Follow-up job logs
   journalctl -u meister-send-followups.service -n 100
   ```

3. **Test SMTP connection:**
   ```bash
   docker compose exec backend python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'meister.barbershop.erlangen@gmail.com', ['your-email@example.com'])
   ```

### Google Blocking Login

If Google blocks the App Password:

1. Verify 2FA is enabled on the Gmail account
2. Regenerate the App Password
3. Check for security notifications in the Gmail account
4. Verify the App Password was created for "Mail" (not "Other")

### Follow-up Emails Not Being Sent

1. **Check if timer is running:**
   ```bash
   systemctl is-active meister-send-followups.timer
   ```

2. **Check for eligible appointments:**
   ```bash
   docker compose exec backend python manage.py send_followups --dry-run
   ```

3. **Verify followup_sent field:**
   ```bash
   docker compose exec backend python manage.py shell
   >>> from bookings.models import Appointment
   >>> Appointment.objects.filter(followup_sent=False).count()
   ```

## Security Notes

- The `.env` file should have permissions `640` or `600`
- Never commit the Gmail App Password to git
- Never log or print the App Password
- The App Password should only be accessible to the backend container

## Monitoring

### Email Send Logs

All email sends are logged with the following information:
- Timestamp
- Subject
- Recipients
- Success/failure status
- Error messages (if failed)

**View email logs:**
```bash
docker compose logs backend | grep "Email sent"
docker compose logs backend | grep "Failed to send email"
```

### Review Request Tracking

Check follow-up email statistics:

```bash
docker compose exec backend python manage.py shell
>>> from bookings.models import Appointment
>>> from django.utils import timezone
>>> from datetime import timedelta

# Total appointments
>>> Appointment.objects.count()

# Follow-ups sent
>>> Appointment.objects.filter(followup_sent=True).count()

# Pending follow-ups (older than 2 hours)
>>> cutoff = timezone.now() - timedelta(hours=2)
>>> Appointment.objects.filter(followup_sent=False, created_at__lte=cutoff).count()
```

## Rate Limiting

The follow-up job has a built-in rate limit of 50 emails per run to avoid overwhelming the SMTP server.

This limit can be adjusted with the `--max-emails` parameter.

## Support

For issues or questions about the email system, check:

1. This README
2. Backend container logs: `docker compose logs backend`
3. Follow-up job logs: `journalctl -u meister-send-followups.service`
4. Django admin panel for appointment data
