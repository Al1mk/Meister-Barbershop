#!/bin/sh
# Custom entrypoint wrapper for nginx reverse-proxy
# Validates configuration before starting nginx

set -e

echo "================================================"
echo "Meister Barbershop Reverse Proxy - Starting..."
echo "================================================"

# Run validation script
if [ -f /usr/local/bin/validate-config.sh ]; then
    echo "Running pre-flight configuration validation..."
    if /usr/local/bin/validate-config.sh /etc/nginx/nginx.conf; then
        echo "✓ Configuration validation passed"
    else
        echo "✗ Configuration validation FAILED"
        echo "Refusing to start nginx with invalid configuration"
        exit 1
    fi
else
    echo "WARNING: validate-config.sh not found, skipping validation"
fi

echo ""
echo "Starting nginx..."
echo "================================================"

# Execute the original nginx entrypoint
exec /docker-entrypoint.sh "$@"
