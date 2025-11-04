#!/bin/bash
# Enhanced health monitoring with auto-recovery and Telegram alerts
# Checks HTTP/HTTPS endpoints and auto-restarts reverse-proxy on failure

set -euo pipefail

DOMAIN="${DOMAIN:-meisterbarbershop.de}"
LOG_TAG="meister-health"
TIMEOUT=10
SUCCESS=true
ALERT_SENT=false
RECOVERY_ATTEMPTED=false

# Throttling: Don't send duplicate alerts within 15 minutes
ALERT_THROTTLE_FILE="/var/tmp/meister-last-alert"
ALERT_THROTTLE_SECONDS=900  # 15 minutes
RECOVERY_THROTTLE_FILE="/var/tmp/meister-last-recovery"

# Paths
TELEGRAM_SCRIPT="/usr/local/bin/send-telegram.sh"
COMPOSE_DIR="/srv/meister"

log() {
    echo "[$(date -Iseconds)] $*"
    logger -t "$LOG_TAG" "$*"
}

send_alert() {
    local message="$1"

    # Check if we should throttle
    if [ -f "$ALERT_THROTTLE_FILE" ]; then
        local last_alert
        last_alert=$(cat "$ALERT_THROTTLE_FILE")
        local current_time
        current_time=$(date +%s)
        local time_diff=$((current_time - last_alert))

        if [ "$time_diff" -lt "$ALERT_THROTTLE_SECONDS" ]; then
            log "Throttling alert (last sent $time_diff seconds ago, threshold: $ALERT_THROTTLE_SECONDS)"
            return 0
        fi
    fi

    # Send alert
    if [ -x "$TELEGRAM_SCRIPT" ]; then
        if "$TELEGRAM_SCRIPT" "$message" 2>&1 | tee -a /var/log/meister-alerts.log; then
            log "Alert sent: $message"
            echo "$(date +%s)" > "$ALERT_THROTTLE_FILE"
            ALERT_SENT=true
        else
            log "Failed to send alert"
        fi
    else
        log "Telegram script not found or not executable: $TELEGRAM_SCRIPT"
    fi
}

check_endpoint() {
    local url="$1"
    local name="$2"

    if curl -fsS --max-time "$TIMEOUT" -o /dev/null "$url" 2>/dev/null; then
        log "✓ $name is UP"
        return 0
    else
        log "✗ $name is DOWN or unreachable"
        SUCCESS=false
        return 1
    fi
}

attempt_recovery() {
    log "=== ATTEMPTING AUTO-RECOVERY ==="
    RECOVERY_ATTEMPTED=true

    # Check throttling for recovery attempts
    if [ -f "$RECOVERY_THROTTLE_FILE" ]; then
        local last_recovery
        last_recovery=$(cat "$RECOVERY_THROTTLE_FILE")
        local current_time
        current_time=$(date +%s)
        local time_diff=$((current_time - last_recovery))

        if [ "$time_diff" -lt 300 ]; then  # 5 minutes
            log "Skipping recovery attempt (last attempted $time_diff seconds ago)"
            send_alert "🚨 Meister site DOWN but recovery throttled (last attempt $time_diff seconds ago)"
            return 1
        fi
    fi

    echo "$(date +%s)" > "$RECOVERY_THROTTLE_FILE"

    log "Restarting reverse-proxy container..."
    if cd "$COMPOSE_DIR" && docker compose restart reverse-proxy 2>&1 | tee -a /var/log/meister-recovery.log; then
        log "Restart command executed successfully"
    else
        log "Failed to execute restart command"
        send_alert "🚨 Meister site DOWN - auto-restart FAILED!"
        return 1
    fi

    log "Waiting 10 seconds for service to stabilize..."
    sleep 10

    # Verify recovery
    log "Verifying site recovery..."
    if curl -fsS --max-time "$TIMEOUT" -o /dev/null "https://$DOMAIN/" 2>/dev/null; then
        log "✓ Recovery successful!"
        send_alert "✅ Meister site recovered automatically after brief downtime"
        return 0
    else
        log "✗ Recovery failed - site still unreachable"
        send_alert "🚨 Meister site UNREACHABLE even after auto-restart! Manual intervention required."
        return 1
    fi
}

# Main health check sequence
log "Starting health check for $DOMAIN"

# Check HTTPS (primary)
if ! check_endpoint "https://$DOMAIN/" "HTTPS root"; then
    # Primary check failed - attempt recovery
    attempt_recovery
    # Exit here since we've handled the failure
    exit $?
fi

# Check HTTP redirect (should return 301)
if curl -fsS --max-time "$TIMEOUT" -o /dev/null -w "%{http_code}" "http://$DOMAIN/" 2>/dev/null | grep -q "301"; then
    log "✓ HTTP redirect working"
else
    log "✗ HTTP redirect not working (but HTTPS is up, not critical)"
fi

# Check API endpoint
if ! check_endpoint "https://$DOMAIN/api/" "API endpoint"; then
    log "WARNING: API endpoint down but main site is up"
fi

# Check healthz endpoint
if ! check_endpoint "https://$DOMAIN/healthz" "Healthz endpoint"; then
    log "WARNING: Healthz endpoint down but main site is up"
fi

# Check media files (barber images)
log "Running media regression guard..."
if /usr/local/bin/media-guard.sh 2>&1 | grep -v "^$"; then
    log "✓ Media guard passed"
else
    log "WARNING: Media guard check had issues (non-critical)"
fi

if [ "$SUCCESS" = true ]; then
    log "=== All health checks PASSED ==="

    # Clear recovery throttle on successful check
    if [ -f "$RECOVERY_THROTTLE_FILE" ]; then
        rm -f "$RECOVERY_THROTTLE_FILE"
    fi

    exit 0
else
    log "=== Some health checks FAILED (but HTTPS is working) ==="
    exit 0  # Don't trigger recovery for non-critical failures
fi
