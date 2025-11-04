# Monitoring & Config Validation with Auto-Recovery

This directory contains monitoring, validation, and auto-recovery tools for meisterbarbershop.de.

## 🆕 Enhanced Features (v2)

- ✅ **Auto-Recovery**: Automatically restarts reverse-proxy on failure
- ✅ **Telegram Alerts**: Real-time notifications to group chat
- ✅ **Smart Throttling**: Prevents alert spam (15-minute cooldown)
- ✅ **Zero Downtime**: Backend and database remain unaffected

## Components

### 1. Nginx Config Validation (`../reverse-proxy/validate-config.sh`)

Validates nginx configuration before deployment to prevent misconfigurations:

- ✅ Syntax check (`nginx -t`)
- ✅ HTTPS server block presence
- ✅ SSL certificate configuration
- ✅ Security headers
- ✅ Automatic config backups

**Used by:**
- Container entrypoint (validates on startup)
- Can be run manually before deployment

### 2. Health Monitoring with Auto-Recovery (`health-check.sh`)

Monitors website availability every 1 minute with automatic recovery:

- ✅ HTTPS endpoint availability
- ✅ HTTP to HTTPS redirect
- ✅ API endpoint health
- ✅ **Auto-restart** reverse-proxy on failure
- ✅ **Telegram alerts** on downtime/recovery
- ✅ Smart throttling (15-minute cooldown)

**Recovery Flow:**
1. Detects HTTPS failure
2. Restarts reverse-proxy container
3. Waits 10 seconds
4. Verifies recovery
5. Sends Telegram alert with status

**Installation:**
```bash
sudo bash install-monitoring-v2.sh
```

**View logs:**
```bash
journalctl -u meister-health.service -f
tail -f /var/log/meister-recovery.log
tail -f /var/log/meister-alerts.log
```

### 2b. Telegram Notifications (`send-telegram.sh`)

Sends alerts to Telegram group chat (-5050078130):

- Uses existing telegram-bot container
- Endpoint: `http://telegram-bot:8787/notify`
- Automatic fallback to localhost

**Test:**
```bash
/usr/local/bin/send-telegram.sh "🧪 Test message"
```

### 3. TLS Expiry Check (`tls-expiry-check.sh`)

Monitors SSL certificate expiry weekly:

- Checks certificate validity
- Warns 15 days before expiry
- Critical alert 7 days before expiry

**Runs:** Every Monday at 9 AM (via cron)

**View logs:**
```bash
tail -f /var/log/meister-tls-check.log
```

**Manual run:**
```bash
/usr/local/bin/meister-tls-check.sh
```

## Quick Start

### Install Monitoring on Server

```bash
cd /srv/meister/deploy/monitoring
sudo bash install-monitoring.sh
```

### Validate Config Before Deploy

```bash
# Test validation in container
docker exec meister-reverse-proxy-1 /usr/local/bin/validate-config.sh
```

### Check Monitoring Status

```bash
# Health check timer status
systemctl status meister-health.timer

# View next scheduled run
systemctl list-timers meister-health.timer

# View recent health checks
journalctl -u meister-health.service -n 50

# Check TLS expiry
/usr/local/bin/meister-tls-check.sh
```

## Alerting (Optional)

To enable email alerts, edit the scripts and uncomment the mail commands:

1. **health-check.sh** - Line ~45: Uncomment mail command
2. **tls-expiry-check.sh** - Line ~30: Uncomment mail command

Example:
```bash
mail -s "Alert: $DOMAIN health check failed" admin@example.com <<< "Details..."
```

Or integrate with external services:
- UptimeRobot: https://uptimerobot.com
- HealthChecks.io: https://healthchecks.io
- Pingdom: https://pingdom.com

## Testing

### Simulate Bad Config (Should Fail)

```bash
# Comment out HTTPS block in nginx.conf
sed -i 's/^\(\s*listen 443\)/# \1/' deploy/reverse-proxy/nginx.conf

# Try to restart (should fail validation)
docker compose restart reverse-proxy

# Check logs
docker compose logs reverse-proxy
```

### Expected Output:
```
NGINX-GUARD: ERROR: No active 'listen 443 ssl' directive found!
Refusing to start nginx with invalid configuration
```

## Monitoring Schedule

- **Health Check:** Every 1 minute (systemd timer)
- **TLS Expiry:** Every Monday 9 AM (cron)
- **Config Backup:** On every validation (keeps last 10)

## Files

```
deploy/
├── reverse-proxy/
│   ├── validate-config.sh      # Config validation
│   ├── entrypoint.sh            # Container entrypoint wrapper
│   ├── nginx.conf               # Nginx config
│   └── Dockerfile               # Updated with validation
└── monitoring/
    ├── health-check.sh          # HTTP/HTTPS health checks
    ├── tls-expiry-check.sh      # SSL certificate monitoring
    ├── meister-health.service   # Systemd service
    ├── meister-health.timer     # Systemd timer
    ├── install-monitoring.sh    # Installation script
    └── README.md                # This file
```
