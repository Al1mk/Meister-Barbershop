#!/bin/bash
# Media regression guard for barber images
# Ensures all barber images are accessible

set -euo pipefail

DOMAIN="${DOMAIN:-www.meisterbarbershop.de}"
LOG_TAG="MEDIA-GUARD"
TIMEOUT=10
SUCCESS=true

BARBERS=("ali" "ehsan" "iman" "javad")

log() {
    echo "[$(date -Iseconds)] $LOG_TAG: $*"
    logger -t "$LOG_TAG" "$*"
}

# Check API endpoint
log "Checking /api/barbers/ endpoint..."
if ! curl -fsS --max-time "$TIMEOUT" -o /dev/null "https://$DOMAIN/api/barbers/" 2>/dev/null; then
    log "FAIL: /api/barbers/ endpoint unreachable"
    SUCCESS=false
fi

# Check each barber image
for barber in "${BARBERS[@]}"; do
    img_url="https://$DOMAIN/media/barbers/$barber.jpg"

    response=$(curl -fsS --max-time "$TIMEOUT" -o /dev/null -w "%{http_code} %{size_download}" "$img_url" 2>/dev/null || echo "000 0")
    status=$(echo "$response" | awk '{print $1}')
    length=$(echo "$response" | awk '{print $2}')

    if [ "$status" != "200" ] || [ "$length" = "0" ]; then
        log "FAIL: $barber.jpg - status=$status length=$length"
        SUCCESS=false
    else
        log "OK: $barber.jpg - status=$status length=$length"
    fi
done

if [ "$SUCCESS" = true ]; then
    log "=== All media checks PASSED ==="
    exit 0
else
    log "=== Some media checks FAILED ==="
    exit 1
fi
