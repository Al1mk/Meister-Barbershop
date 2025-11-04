#!/bin/bash
# Installation script for monitoring services
# Run as root: sudo bash install-monitoring.sh

set -euo pipefail

echo "================================================"
echo "Installing Meister Barbershop Monitoring"
echo "================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install health check script
echo "Installing health check script..."
cp "$SCRIPT_DIR/health-check.sh" /usr/local/bin/meister-health-check.sh
chmod +x /usr/local/bin/meister-health-check.sh
echo "✓ Health check script installed"

# Install TLS expiry check script
echo "Installing TLS expiry check script..."
cp "$SCRIPT_DIR/tls-expiry-check.sh" /usr/local/bin/meister-tls-check.sh
chmod +x /usr/local/bin/meister-tls-check.sh
echo "✓ TLS expiry check script installed"

# Install systemd service and timer
echo "Installing systemd service and timer..."
cp "$SCRIPT_DIR/meister-health.service" /etc/systemd/system/
cp "$SCRIPT_DIR/meister-health.timer" /etc/systemd/system/
systemctl daemon-reload
echo "✓ Systemd units installed"

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
echo "Status:"
systemctl status meister-health.timer --no-pager || true
echo ""
echo "Next health check run:"
systemctl list-timers meister-health.timer --no-pager || true
echo ""
echo "To view health check logs:"
echo "  journalctl -u meister-health.service -f"
echo ""
echo "To view TLS check logs:"
echo "  tail -f /var/log/meister-tls-check.log"
echo ""
echo "To manually run checks:"
echo "  /usr/local/bin/meister-health-check.sh"
echo "  /usr/local/bin/meister-tls-check.sh"
