#!/bin/bash
# Health monitoring script for meisterbarbershop.de
# Checks HTTP/HTTPS endpoints and logs failures

set -euo pipefail

DOMAIN="${DOMAIN:-meisterbarbershop.de}"
LOG_TAG="meister-health"
TIMEOUT=10
SUCCESS=true

log() {
    echo "[$(date -Iseconds)] $*"
    logger -t "$LOG_TAG" "$*"
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

log "Starting health check for $DOMAIN"

# Check HTTPS (primary)
check_endpoint "https://$DOMAIN/" "HTTPS root"

# Check HTTP (should redirect)
if curl -fsS --max-time "$TIMEOUT" -o /dev/null -w "%{http_code}" "http://$DOMAIN/" 2>/dev/null | grep -q "301"; then
    log "✓ HTTP redirect working"
else
    log "✗ HTTP redirect not working"
    SUCCESS=false
fi

# Check API endpoint
check_endpoint "https://$DOMAIN/api/" "API endpoint"

# Check healthz endpoint
check_endpoint "https://$DOMAIN/healthz" "Healthz endpoint"

if [ "$SUCCESS" = true ]; then
    log "=== All health checks PASSED ==="
    exit 0
else
    log "=== Some health checks FAILED ==="

    # Send alert (customize this section)
    # Example: send email, webhook, etc.
    # mail -s "Alert: $DOMAIN health check failed" admin@example.com <<< "Health check failed at $(date)"

    exit 1
fi
