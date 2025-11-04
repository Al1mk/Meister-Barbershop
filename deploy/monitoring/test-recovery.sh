#!/bin/bash
# Test script for auto-recovery and Telegram alerts
# Run as root on the server

set -euo pipefail

echo "================================================"
echo "Testing Auto-Recovery and Telegram Alerts"
echo "================================================"

# Test 1: Telegram notification
echo ""
echo "Test 1: Sending test Telegram notification..."
if /usr/local/bin/send-telegram.sh "🧪 Test alert from Meister monitoring system"; then
    echo "✓ Telegram test sent"
else
    echo "✗ Telegram test failed"
fi

sleep 3

# Test 2: Manual health check
echo ""
echo "Test 2: Running manual health check..."
if /usr/local/bin/meister-health-check.sh; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
fi

sleep 3

# Test 3: Check systemd timer status
echo ""
echo "Test 3: Checking systemd timer status..."
systemctl status meister-health.timer --no-pager

echo ""
echo "Test 4: Checking next scheduled run..."
systemctl list-timers meister-health.timer --no-pager

echo ""
echo "Test 5: Recent health check logs..."
journalctl -u meister-health.service -n 20 --no-pager

echo ""
echo "================================================"
echo "Testing Complete"
echo "================================================"
echo ""
echo "To simulate a failure and test auto-recovery:"
echo "  1. Stop reverse-proxy: docker compose stop reverse-proxy"
echo "  2. Wait 1 minute for health check to run"
echo "  3. Check logs: journalctl -u meister-health.service -f"
echo "  4. Check Telegram for recovery alert"
echo ""
echo "Log files:"
echo "  /var/log/meister-alerts.log"
echo "  /var/log/meister-recovery.log"
