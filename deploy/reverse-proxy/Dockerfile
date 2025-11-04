# syntax=docker/dockerfile:1

FROM nginx:1.27-alpine

# Install required utilities
RUN apk add --no-cache curl openssl

# Copy validation and entrypoint scripts
COPY validate-config.sh /usr/local/bin/validate-config.sh
COPY entrypoint.sh /usr/local/bin/entrypoint-wrapper.sh
COPY nginx.conf /etc/nginx/nginx.conf

# Make scripts executable
RUN chmod +x /usr/local/bin/validate-config.sh /usr/local/bin/entrypoint-wrapper.sh

# Use custom entrypoint that validates config before starting
ENTRYPOINT ["/usr/local/bin/entrypoint-wrapper.sh"]
CMD ["nginx", "-g", "daemon off;"]

# Enhanced healthcheck: verify both HTTP and HTTPS endpoints
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
    CMD curl -fsS http://127.0.0.1/healthz && curl -fsSk https://127.0.0.1/healthz || exit 1
