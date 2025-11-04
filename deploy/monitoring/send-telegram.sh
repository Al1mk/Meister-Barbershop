#!/bin/bash
# Telegram notification script for Meister Barbershop monitoring
# Sends alerts via the existing telegram-bot container

set -euo pipefail

MESSAGE="${1:-Test notification from Meister monitoring}"
ENV_FILE="${TELEGRAM_ENV_FILE:-/srv/telegram-bot/.env}"

log() {
    echo "[$(date -Iseconds)] TELEGRAM: $*" >&2
    logger -t meister-telegram "$*"
}

# Load secret from .env file
TELEGRAM_BOT_SECRET=""
if [ -f "$ENV_FILE" ]; then
    # Source the env file to get TELEGRAM_BOT_SECRET
    TELEGRAM_BOT_SECRET=$(grep '^TELEGRAM_BOT_SECRET=' "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

# Function to send notification
send_notification() {
    local container_name="$1"
    local message="$2"
    local secret="$3"

    # Build JSON payload with secret
    local json_payload
    if [ -n "$secret" ]; then
        json_payload=$(jq -n --arg msg "$message" --arg sec "$secret" '{text: $msg, secret: $sec}')
    else
        json_payload=$(jq -n --arg msg "$message" '{text: $msg}')
    fi

    # Use docker exec to call from inside the container network
    if docker exec "$container_name" curl -fsS -X POST http://127.0.0.1:8787/notify \
        -H "Content-Type: application/json" \
        -d "$json_payload" \
        --max-time 10 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

log "Attempting to send Telegram notification"

# Try to find telegram-bot container
TELEGRAM_CONTAINER=$(docker ps --filter "name=telegram-bot" --format "{{.Names}}" | head -1)

if [ -z "$TELEGRAM_CONTAINER" ]; then
    log "✗ telegram-bot container not found"
    exit 1
fi

log "Found container: $TELEGRAM_CONTAINER"

# Send notification
if send_notification "$TELEGRAM_CONTAINER" "$MESSAGE" "$TELEGRAM_BOT_SECRET"; then
    log "✓ Notification sent successfully"
    exit 0
fi

log "✗ Failed to send Telegram notification"
exit 1
