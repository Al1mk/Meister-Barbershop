#!/bin/bash
# Installation script for enhanced monitoring with auto-recovery
# Run as root: sudo bash install-monitoring-v2.sh

set -euo pipefail

echo "================================================"
echo "Installing Meister Barbershop Enhanced Monitoring"
echo "with Auto-Recovery and Telegram Alerts"
echo "================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stop existing timer if running
if systemctl is-active --quiet meister-health.timer; then
    echo "Stopping existing health check timer..."
    systemctl stop meister-health.timer
fi

# Install Telegram notification script
echo "Installing Telegram notification script..."
cp "$SCRIPT_DIR/send-telegram.sh" /usr/local/bin/send-telegram.sh
chmod +x /usr/local/bin/send-telegram.sh
echo "✓ Telegram script installed"

# Install enhanced health check script
echo "Installing enhanced health check script with auto-recovery..."
if [ -f "$SCRIPT_DIR/health-check-v2.sh" ]; then
    cp "$SCRIPT_DIR/health-check-v2.sh" /usr/local/bin/meister-health-check.sh
else
    echo "WARNING: health-check-v2.sh not found, using existing version"
fi
chmod +x /usr/local/bin/meister-health-check.sh
echo "✓ Health check script installed"

# Install TLS expiry check script (unchanged)
echo "Installing TLS expiry check script..."
cp "$SCRIPT_DIR/tls-expiry-check.sh" /usr/local/bin/meister-tls-check.sh
chmod +x /usr/local/bin/meister-tls-check.sh
echo "✓ TLS expiry check script installed"

# Install systemd service and timer
echo "Installing systemd service and timer..."
if [ -f "$SCRIPT_DIR/meister-health-v2.service" ]; then
    cp "$SCRIPT_DIR/meister-health-v2.service" /etc/systemd/system/meister-health.service
else
    echo "WARNING: meister-health-v2.service not found, using existing version"
fi
cp "$SCRIPT_DIR/meister-health.timer" /etc/systemd/system/
systemctl daemon-reload
echo "✓ Systemd units installed"

# Create log directory
mkdir -p /var/log
touch /var/log/meister-alerts.log
touch /var/log/meister-recovery.log
chmod 644 /var/log/meister-alerts.log /var/log/meister-recovery.log

# Enable and start timer
echo "Enabling and starting health check timer..."
systemctl enable meister-health.timer
systemctl start meister-health.timer
echo "✓ Health check timer started"

# Setup cron job for TLS expiry check (weekly, Mondays at 9 AM)
echo "Setting up TLS expiry check cron job..."
CRON_LINE="0 9 * * 1 /usr/local/bin/meister-tls-check.sh >> /var/log/meister-tls-check.log 2>&1"
(crontab -l 2>/dev/null | grep -v meister-tls-check.sh; echo "$CRON_LINE") | crontab -
echo "✓ TLS expiry cron job installed (Mondays at 9 AM)"

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "✨ New Features:"
echo "  • Auto-recovery: Restarts reverse-proxy on failure"
echo "  • Telegram alerts: Sends notifications to chat -5050078130"
echo "  • Throttling: Max 1 alert per 15 minutes"
echo "  • Recovery logs: /var/log/meister-recovery.log"
echo ""
echo "Status:"
systemctl status meister-health.timer --no-pager || true
echo ""
echo "Next health check run:"
systemctl list-timers meister-health.timer --no-pager || true
echo ""
echo "Logs:"
echo "  Health checks:   journalctl -u meister-health.service -f"
echo "  Alerts:          tail -f /var/log/meister-alerts.log"
echo "  Recovery:        tail -f /var/log/meister-recovery.log"
echo "  TLS checks:      tail -f /var/log/meister-tls-check.log"
echo ""
echo "Manual commands:"
echo "  Test health:     /usr/local/bin/meister-health-check.sh"
echo "  Send test alert: /usr/local/bin/send-telegram.sh 'Test message'"
echo "  Check TLS:       /usr/local/bin/meister-tls-check.sh"
echo ""
echo "🚀 Auto-recovery monitoring is now active!"
