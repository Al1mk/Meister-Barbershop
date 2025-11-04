# Telegram Notify Service

Secure Telegram notification service for Meister Barbershop production server.

## Service Information

- **Service Name**: telegram-notify.service
- **Endpoint**: http://127.0.0.1:8787/notify
- **Binding**: Localhost only (127.0.0.1)
- **User**: telegram (system user, no-login)
- **Logs**: /var/log/telegram-notify.log (rotated daily, 7 days retention)

## Setup Requirements

### 1. Add Bot to Telegram Group

Before the bot can send messages, you must add it to your Telegram group:

1. Open Telegram and go to your target group
2. Click on the group name to open group settings
3. Select "Add Members"
4. Search for your bot by username (use @BotFather to find the bot username)
5. Add the bot to the group
6. Make sure the bot has permission to send messages

### 2. Verify Bot Permissions

The bot needs the following permissions in the group:
- Send messages
- Send photos (if you plan to send images)

## Usage

### Send Simple Text Notification

```bash
BOT_SECRET=$(grep "^BOT_SECRET=" /srv/telegram-bot/.env | cut -d= -f2)

curl -X POST http://127.0.0.1:8787/notify \
  -H "Content-Type: application/json" \
  -d "{\"secret\":\"$BOT_SECRET\", \"text\":\"Your notification message here\"}"
```

### Send Appointment Notification

```bash
BOT_SECRET=$(grep "^BOT_SECRET=" /srv/telegram-bot/.env | cut -d= -f2)

curl -X POST http://127.0.0.1:8787/notify \
  -H "Content-Type: application/json" \
  -d "{
    \"secret\":\"$BOT_SECRET\",
    \"appointment\": {
      \"id\": \"12345\",
      \"customer\": \"John Doe\",
      \"barber\": \"Max\",
      \"time\": \"2025-11-03 14:30\",
      \"service\": \"Haircut + Beard\",
      \"notes\": \"First time customer\"
    }
  }"
```

### Response Format

**Success:**
```json
{
  "ok": true,
  "result": {...}
}
```

**Error:**
```json
{
  "ok": false,
  "error": "Error description"
}
```

## Security

- **BOT_SECRET**: Required for all API calls. Stored in /srv/telegram-bot/.env (mode 640, root:telegram)
- **Localhost Only**: Service binds to 127.0.0.1 only - not accessible from external networks
- **IP Validation**: Endpoint rejects requests from non-localhost IPs
- **No Secrets in Logs**: Bot token and secrets are never logged

### Rotating BOT_SECRET

To rotate the secret:

```bash
# Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# Update .env file
sed -i "s/^BOT_SECRET=.*/BOT_SECRET=$NEW_SECRET/" /srv/telegram-bot/.env

# Restart service
systemctl restart telegram-notify.service

# Update your backend/scripts with the new secret
```

## Service Management

```bash
# Check status
systemctl status telegram-notify.service

# View logs
journalctl -u telegram-notify.service -f

# Restart service
systemctl restart telegram-notify.service

# Stop service
systemctl stop telegram-notify.service

# Start service
systemctl start telegram-notify.service
```

## Integration with Backend

To integrate with your Django backend, add the following to your appointment creation logic:

```python
import requests
import os

def notify_telegram_new_appointment(appointment):
    """Send Telegram notification for new appointment"""
    bot_secret = os.getenv("TELEGRAM_BOT_SECRET")  # Add to backend .env
    
    payload = {
        "secret": bot_secret,
        "appointment": {
            "id": appointment.id,
            "customer": appointment.customer_name,
            "barber": appointment.barber.name,
            "time": appointment.start_time.strftime("%Y-%m-%d %H:%M"),
            "service": appointment.service.name,
            "notes": appointment.notes or ""
        }
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8787/notify",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Log error but don't fail the appointment creation
        print(f"Failed to send Telegram notification: {e}")
        return None
```

## Troubleshooting

### "Chat not found" error

This means the bot hasn't been added to the Telegram group yet. Follow the setup instructions above.

### Permission denied errors

Check file permissions:
```bash
ls -l /srv/telegram-bot/.env  # Should be: -rw-r----- root telegram
ls -ld /srv/telegram-bot       # Should be: drwxr-x--- telegram telegram
```

### Service won't start

Check logs:
```bash
journalctl -u telegram-notify.service -n 50
```

Common issues:
- Missing python3-venv package
- Incorrect .env file permissions
- Invalid BOT_TOKEN or GROUP_ID

## Files and Directories

```
/srv/telegram-bot/
├── .env                    # Environment variables (secrets)
├── app.py                  # FastAPI application
├── venv/                   # Python virtual environment
└── README.md              # This file

/etc/systemd/system/
└── telegram-notify.service # Systemd service unit

/etc/logrotate.d/
└── telegram-notify         # Log rotation config

/var/log/
└── telegram-notify.log     # Service logs (if configured)
```

## Support

For issues or questions, check:
1. Service logs: `journalctl -u telegram-notify.service`
2. Service status: `systemctl status telegram-notify.service`
3. Port binding: `ss -tlnp | grep 8787`
4. Test endpoint: `curl http://127.0.0.1:8787/notify`
