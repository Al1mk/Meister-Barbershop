#!/bin/sh
# Nginx configuration validation script
# Ensures HTTPS is properly configured before starting/reloading

set -e

CONFIG_FILE="${1:-/etc/nginx/nginx.conf}"
BACKUP_DIR="/etc/nginx/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

log() {
    echo "[$(date -Iseconds)] NGINX-GUARD: $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting nginx configuration validation..."
log "Config file: $CONFIG_FILE"

# 1) Basic syntax check
log "Running nginx -t..."
if ! nginx -t 2>&1; then
    error "nginx -t failed! Configuration has syntax errors."
fi
log "✓ Syntax check passed"

# 2) Check if HTTPS server block is present and active (not commented)
log "Checking for active HTTPS server block..."
if ! grep -qE '^\s*server\s*\{' "$CONFIG_FILE"; then
    error "No server block found in config"
fi

if ! grep -qE '^\s*listen\s+443\s+(ssl|.*ssl)' "$CONFIG_FILE"; then
    error "No active 'listen 443 ssl' directive found! HTTPS is disabled or commented out."
fi
log "✓ HTTPS listener found"

# 3) Check for SSL certificate configuration
log "Checking SSL certificate paths..."
if ! grep -qE '^\s*ssl_certificate\s+.*meisterbarbershop\.de' "$CONFIG_FILE"; then
    log "WARNING: SSL certificate path doesn't reference meisterbarbershop.de domain"
fi

if ! grep -qE '^\s*ssl_certificate_key\s+' "$CONFIG_FILE"; then
    error "No ssl_certificate_key directive found!"
fi
log "✓ SSL certificate configuration found"

# 4) Check for required security headers (optional, warn only)
log "Checking security headers..."
if ! grep -q "Strict-Transport-Security" "$CONFIG_FILE"; then
    log "WARNING: HSTS header not configured"
else
    log "✓ HSTS header configured"
fi

# 5) Verify upstream services are defined
log "Checking upstream services..."
if ! grep -q "upstream backend_service" "$CONFIG_FILE"; then
    log "WARNING: backend_service upstream not found"
fi
if ! grep -q "upstream frontend_service" "$CONFIG_FILE"; then
    log "WARNING: frontend_service upstream not found"
fi
log "✓ Upstream services configured"

# 6) Create backup of validated config
BACKUP_FILE="$BACKUP_DIR/nginx.conf.backup-$TIMESTAMP"
cp "$CONFIG_FILE" "$BACKUP_FILE"
log "✓ Config backed up to $BACKUP_FILE"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/nginx.conf.backup-* 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

log "=== All validation checks passed ==="
log "Configuration is safe to use"
exit 0
