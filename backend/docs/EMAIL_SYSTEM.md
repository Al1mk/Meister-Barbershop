# Email System Documentation

## Overview

The Meister Barbershop email system sends automated appointment confirmations and 2-hour follow-up emails requesting Google reviews. The system is hardened with:

- **Domain authentication** (SPF/DKIM/DMARC)
- **Transactional email providers** (Mailgun or Sendgrid with domain DKIM)
- **GDPR compliance** (unsubscribe links, opt-out tracking, IP logging)
- **Bounce/complaint handling** (automatic opt-outs)
- **60-day cooldown** period per email
- **ONE follow-up per appointment** (not per email)
- **Telegram alerts** for high failure rates (>5%)
- **Comprehensive metrics** endpoint

## Architecture

### Email Flow

1. **Appointment Confirmation** (immediate)
   - Sent when appointment is created
   - Includes ICS calendar attachment
   - Bilingual (DE + EN)

2. **Follow-up Review Request** (2 hours after appointment start)
   - Only sent if appointment status is `completed` or `attended`
   - Includes Google Review link with UTM parameters
   - Includes List-Unsubscribe header (RFC 8058 compliant)
   - ONE follow-up per appointment
   - 60-day cooldown per email address

### Components

- `bookings/models.py:FollowUpRequest` - Tracks sent emails, opt-outs, bounces
- `bookings/management/commands/send_followups.py` - Periodic job to send follow-ups
- `bookings/utils/email_helpers.py` - Email sending with List-Unsubscribe headers
- `bookings/utils/ics_generator.py` - ICS calendar file generation
- `bookings/unsubscribe_views.py` - GDPR-compliant unsubscribe handling
- `bookings/webhook_views.py` - Bounce/complaint webhooks
- `bookings/metrics_views.py` - Health metrics endpoint

## Configuration

### Environment Variables

Add to `/srv/meister/backend/.env`:

```bash
# Email Provider (mailgun or sendgrid - leave empty for Gmail fallback)
EMAIL_PROVIDER=mailgun
EMAIL_API_KEY=key-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
EMAIL_DOMAIN=meisterbarbershop.de
EMAIL_FROM=Meister Barbershop <no-reply@meisterbarbershop.de>

# Email System Configuration
FOLLOWUP_EMAIL_COOLDOWN_DAYS=60
SITE_URL=https://www.meisterbarbershop.de
SITE_IMPRINT_URL=https://www.meisterbarbershop.de/impressum
SITE_PRIVACY_URL=https://www.meisterbarbershop.de/datenschutz

# Telegram Alerts
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=-1001234567890

# Google Reviews
GOOGLE_PLACE_ID=ChIJRWUULEz5oUcRhfnp-cp0dXs
```

### DNS Records for Domain Authentication

#### SPF Record

Add TXT record for `meisterbarbershop.de`:

**For Mailgun:**
```
v=spf1 include:mailgun.org ~all
```

**For Sendgrid:**
```
v=spf1 include:sendgrid.net ~all
```

**For Gmail SMTP (fallback):**
```
v=spf1 include:_spf.google.com ~all
```

#### DKIM Records

**Mailgun:**
1. Log in to Mailgun dashboard
2. Navigate to Sending > Domains
3. Add domain `meisterbarbershop.de`
4. Copy the TXT records provided (usually 2 records):
   - `k1._domainkey.meisterbarbershop.de` TXT `k=rsa; p=MIGfMA0GCS...`
   - `smtp._domainkey.meisterbarbershop.de` TXT `k=rsa; p=MIGfMA0GCS...`

**Sendgrid:**
1. Log in to Sendgrid dashboard
2. Settings > Sender Authentication
3. Authenticate your domain: `meisterbarbershop.de`
4. Add the 3 CNAME records provided:
   - `s1._domainkey.meisterbarbershop.de` CNAME `s1.domainkey.uXXXXXXX.wl.sendgrid.net`
   - `s2._domainkey.meisterbarbershop.de` CNAME `s2.domainkey.uXXXXXXX.wl.sendgrid.net`
   - `em1234.meisterbarbershop.de` CNAME `uXXXXXXX.wl.sendgrid.net`

#### DMARC Record

Add TXT record for `_dmarc.meisterbarbershop.de`:

```
v=DMARC1; p=quarantine; rua=mailto:dmarc@meisterbarbershop.de; ruf=mailto:dmarc@meisterbarbershop.de; fo=1; adkim=r; aspf=r; pct=100
```

**Explanation:**
- `p=quarantine`: Quarantine emails that fail DMARC (change to `p=reject` after testing)
- `rua`: Aggregate reports sent to this email
- `ruf`: Forensic reports sent to this email
- `fo=1`: Generate forensic reports on any failure
- `adkim=r`: Relaxed DKIM alignment
- `aspf=r`: Relaxed SPF alignment

### Webhook Configuration

#### Mailgun Webhooks

1. Log in to Mailgun dashboard
2. Navigate to Sending > Webhooks
3. Add webhooks:
   - **Permanent Failures**: `https://www.meisterbarbershop.de/email-webhook/mailgun/`
   - **Temporary Failures**: `https://www.meisterbarbershop.de/email-webhook/mailgun/`
   - **Complaints**: `https://www.meisterbarbershop.de/email-webhook/mailgun/`

#### Sendgrid Webhooks

1. Log in to Sendgrid dashboard
2. Settings > Mail Settings > Event Webhook
3. Enable and set:
   - **HTTP POST URL**: `https://www.meisterbarbershop.de/email-webhook/sendgrid/`
   - **Events to POST**: Bounced, Dropped, Spam Reports, Unsubscribe

## Management Commands

### send_followups

Send 2-hour follow-up emails requesting Google reviews.

**Dry-run (recommended first):**
```bash
docker compose exec backend python manage.py send_followups --dry-run
```

**Production run:**
```bash
docker compose exec backend python manage.py send_followups
```

**Options:**
- `--dry-run`: Show what would be sent without sending emails
- `--max-emails N`: Limit to N emails per run (default: 50)

**Output example:**
```
Found 12 appointment(s) eligible for follow-up, 8 skipped

Skipped appointments:
  Appointment 5: Status is 'booked' (need completed/attended)
  Appointment 7: Cooldown active (last follow-up 15 days ago, need 60)
  Appointment 9: Customer opted out
  ...

  Appointment 15: John Doe (john@example.com) - started 2025-11-09 14:00 - status: completed
    ✓ Follow-up email sent
  ...

Summary: 12 sent, 0 failed (0.0% failure rate)
```

### Systemd Timer (Automated)

The systemd timer runs every 5 minutes:

```bash
# Check timer status
systemctl status meister-followup.timer

# View recent logs
journalctl -u meister-followup.service -n 50 --no-pager
```

## Endpoints

### Health & Metrics

**GET `/health/email-metrics/`**

Returns JSON with email system health metrics:

```json
{
  "status": "ok",
  "timestamp": "2025-11-09T15:30:00+01:00",
  "last_run_at": "2025-11-09T15:25:00+01:00",
  "sent_count_24h": 15,
  "sent_count_7d": 89,
  "opt_out_count": 3,
  "bounce_count": 1,
  "complaint_count": 0,
  "cooldown_active_count": 45,
  "cooldown_period_days": 60
}
```

### Unsubscribe

**GET `/unsubscribe-followup/?email=customer@example.com&token=abc123`**

Displays bilingual confirmation page (DE first, EN second).

**POST `/unsubscribe-followup/`**

Processes opt-out with IP tracking and audit logging.

**Token Expiry:** 48 hours. If expired, generates new token for one-click confirm.

### Webhooks

**POST `/email-webhook/mailgun/`**

Handles Mailgun bounce/complaint events.

**POST `/email-webhook/sendgrid/`**

Handles Sendgrid bounce/complaint events.

## Follow-up Logic

### Eligibility Criteria

An appointment is eligible for follow-up if:

1. ✅ Appointment status is `completed` or `attended`
2. ✅ Appointment start time is at least 2 hours ago
3. ✅ Appointment does NOT have a FollowUpRequest record (ONE per appointment)
4. ✅ Customer has email address
5. ✅ Customer email is NOT opted out
6. ✅ Customer email did NOT receive a follow-up within last 60 days (cooldown)

### Skip Reasons

In dry-run mode, the command shows detailed skip reasons:

- `Status is 'booked' (need completed/attended)` - Appointment not yet attended
- `Cooldown active (last follow-up 15 days ago, need 60)` - Too soon since last email
- `Customer opted out` - Customer unsubscribed
- `Follow-up already sent for this appointment` - Already sent for this specific appointment
- `Appointment start time < 2 hours ago` - Too soon after appointment

## Monitoring

### Logs

All email activity is logged to `/var/log/meister-email.log`:

```bash
# Tail email logs
tail -f /var/log/meister-email.log

# Search for failures
grep "Failed to send" /var/log/meister-email.log

# Search for opt-outs
grep "opted out" /var/log/meister-email.log
```

### Telegram Alerts

Automatic alerts sent to Telegram group when:

- Failure rate > 5% in a single run
- Example alert:

```
⚠️ Email System Alert

High failure rate detected in follow-up emails:
• Sent: 10
• Failed: 2
• Failure rate: 16.7%

Please check `/var/log/meister-email.log` for details.
```

### Django Admin

View and manage FollowUpRequest records:

`https://www.meisterbarbershop.de/admin/bookings/followuprequest/`

Fields:
- Email, phone, appointment link
- Sent timestamp
- Opt-out status, timestamp, IP
- Bounce type (hard/soft)
- Spam complaint flag
- Raw webhook event data (JSON)

## Testing

### Unit Tests

Run comprehensive test suite:

```bash
docker compose exec backend python manage.py test bookings.tests.test_followups
```

Tests cover:
- Cooldown logic
- Status filtering (completed/attended only)
- Timezone handling (Europe/Berlin)
- Unsubscribe token validation & expiry
- ICS calendar generation
- Per-appointment follow-up logic

### Manual Testing

1. **Create test appointment:**
   ```python
   from bookings.models import Appointment, Customer
   from barbers.models import Barber
   from django.utils import timezone
   import pytz

   barber = Barber.objects.first()
   customer = Customer.objects.create(
       name="Test User",
       email="your-test-email@example.com",
       phone="+491234567890"
   )

   berlin_tz = pytz.timezone('Europe/Berlin')
   now = timezone.now().astimezone(berlin_tz)

   appt = Appointment.objects.create(
       barber=barber,
       customer=customer,
       start_at=now - timedelta(hours=3),  # 3 hours ago
       end_at=now - timedelta(hours=2, minutes=30),
       service_type="haircut",
       duration_minutes=30,
       status="completed"  # IMPORTANT: must be completed or attended
   )
   ```

2. **Run dry-run:**
   ```bash
   docker compose exec backend python manage.py send_followups --dry-run
   ```

3. **Send real email:**
   ```bash
   docker compose exec backend python manage.py send_followups --max-emails=1
   ```

4. **Test unsubscribe link** from email received

5. **Check metrics:**
   ```bash
   curl https://www.meisterbarbershop.de/health/email-metrics/
   ```

## Troubleshooting

### No emails being sent

1. Check appointment status:
   ```python
   from bookings.models import Appointment
   Appointment.objects.filter(status__in=['completed', 'attended']).count()
   ```

2. Check for existing follow-ups:
   ```python
   from bookings.models import FollowUpRequest
   FollowUpRequest.objects.count()
   ```

3. Run dry-run for detailed skip reasons:
   ```bash
   docker compose exec backend python manage.py send_followups --dry-run
   ```

### High bounce rate

1. Check bounce types in admin: `/admin/bookings/followuprequest/`
2. Review webhook event data (JSON field)
3. Verify DNS records (SPF/DKIM/DMARC) using [MXToolbox](https://mxtoolbox.com/)

### Email provider errors

**Mailgun 401 Unauthorized:**
- Verify `EMAIL_API_KEY` in `.env`
- Check API key permissions in Mailgun dashboard

**Sendgrid 403 Forbidden:**
- Verify `EMAIL_API_KEY` has "Mail Send" permission
- Check sender authentication status

### Gmail fallback not working

1. Verify App Password in `.env`:
   ```bash
   docker compose exec backend env | grep EMAIL
   ```

2. Test SMTP connection:
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
   ```

## Security Best Practices

1. **Never commit secrets** - Use `.env` file (`.gitignore`d)
2. **Rotate API keys** regularly (every 90 days)
3. **Monitor webhook endpoints** for abuse
4. **Set file permissions** for `.env`: `chmod 640 .env`
5. **Enable 2FA** on email provider accounts
6. **Review opt-outs** monthly in Django admin
7. **Validate DMARC reports** weekly

## Compliance (GDPR)

- ✅ **Unsubscribe link** in every email (RFC 8058 List-Unsubscribe header)
- ✅ **48-hour token expiry** for unsubscribe links
- ✅ **IP address logging** for opt-out actions
- ✅ **Audit trail** (webhook events stored as JSON)
- ✅ **Right to be forgotten** (opt-out = no more emails)
- ✅ **Privacy policy link** in email footer
- ✅ **Imprint link** in email footer (German legal requirement)

## Performance

- **Rate limiting:** 50 emails per run (configurable via `--max-emails`)
- **Systemd timer:** Runs every 5 minutes
- **Database indexes:** email, opt_out, sent_at fields
- **Query optimization:** select_related for barber/customer joins
- **Log rotation:** 10MB max, 5 backups

## Support

For issues or questions:
- Check logs: `/var/log/meister-email.log`
- Review metrics: `https://www.meisterbarbershop.de/health/email-metrics/`
- Email: meister.barbershop.erlangen@gmail.com
