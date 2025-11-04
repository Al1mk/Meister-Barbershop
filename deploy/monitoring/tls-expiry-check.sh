#!/bin/bash
# TLS certificate expiry monitoring for meisterbarbershop.de
# Warns when certificate is expiring soon

set -euo pipefail

DOMAIN="${DOMAIN:-meisterbarbershop.de}"
LOG_TAG="meister-tls"
WARNING_DAYS=15
CRITICAL_DAYS=7

log() {
    echo "[$(date -Iseconds)] $*"
    logger -t "$LOG_TAG" "$*"
}

alert() {
    log "ALERT: $*"
    # Add custom alerting here (email, webhook, etc.)
    # Example: mail -s "TLS Alert: $DOMAIN" admin@example.com <<< "$*"
}

log "Checking TLS certificate expiry for $DOMAIN"

# Get certificate expiry date
EXPIRY_INFO=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null)

if [ -z "$EXPIRY_INFO" ]; then
    alert "Failed to retrieve certificate information for $DOMAIN"
    exit 1
fi

# Extract date
EXPIRY_DATE=$(echo "$EXPIRY_INFO" | cut -d= -f2)
log "Certificate expires: $EXPIRY_DATE"

# Calculate days until expiry
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

log "Days until expiry: $DAYS_UNTIL_EXPIRY"

if [ "$DAYS_UNTIL_EXPIRY" -lt 0 ]; then
    alert "Certificate EXPIRED ${DAYS_UNTIL_EXPIRY#-} days ago!"
    exit 2
elif [ "$DAYS_UNTIL_EXPIRY" -lt "$CRITICAL_DAYS" ]; then
    alert "Certificate expires in $DAYS_UNTIL_EXPIRY days (CRITICAL)"
    exit 1
elif [ "$DAYS_UNTIL_EXPIRY" -lt "$WARNING_DAYS" ]; then
    log "WARNING: Certificate expires in $DAYS_UNTIL_EXPIRY days"
    exit 0
else
    log "✓ Certificate valid for $DAYS_UNTIL_EXPIRY days"
    exit 0
fi
