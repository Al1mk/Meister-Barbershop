#!/bin/bash
# Port conflict monitor - alerts if non-docker process binds 80/443
LOG="/var/log/meister-recovery.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

check_port() {
    local port=$1
    local owner=$(ss -ltnp | grep ":$port " | grep -v "docker-proxy" | awk "{print \$NF}" | head -1)
    if [ -n "$owner" ]; then
        echo "[$DATE] WARNING: Non-docker process binding port $port: $owner" | tee -a "$LOG"
        return 1
    fi
    return 0
}

if check_port 80 && check_port 443; then
    echo "[$DATE] OK: Ports 80 and 443 are clean (docker-proxy only)" >> "$LOG"
else
    echo "[$DATE] ERROR: Port conflict detected! Review immediately." | tee -a "$LOG"
    exit 1
fi
